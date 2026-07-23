"""Single place that maps DomainError → HTTP (LLD §8.5).

No view ever writes a status code for a domain failure. One error envelope everywhere:
    {"error": {"code": "...", "message": "...", "details": {}}}
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

from core.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    InfrastructureError,
    NotFoundError,
    ValidationError,
)

_STATUS_BY_TYPE = [
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (ConflictError, status.HTTP_409_CONFLICT),
    (ValidationError, status.HTTP_400_BAD_REQUEST),
    (AuthorizationError, status.HTTP_403_FORBIDDEN),
    (AuthenticationError, status.HTTP_400_BAD_REQUEST),
    (InfrastructureError, status.HTTP_502_BAD_GATEWAY),
]


def _status_for(exc: DomainError) -> int:
    for cls, code in _STATUS_BY_TYPE:
        if isinstance(exc, cls):
            return code
    return status.HTTP_400_BAD_REQUEST


def domain_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
            status=_status_for(exc),
        )

    # Fall back to DRF for its own exceptions (auth, throttle, validation), then wrap the body
    # in the same envelope so the client sees one shape.
    response = drf_default_handler(exc, context)
    if response is not None:
        code = getattr(exc, "default_code", "error")
        response.data = {"error": {"code": code, "message": _message(response.data), "details": {}}}
    return response


def _message(data) -> str:
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            return str(detail)
        return "; ".join(f"{k}: {v}" for k, v in data.items())
    if isinstance(data, list):
        return "; ".join(str(x) for x in data)
    return str(data)
