"""Single place that maps DomainError → HTTP (LLD §8.5).

No view ever writes a status code for a domain failure. One error envelope everywhere:
    {"error": {"code": "...", "message": "...", "details": {}}}
"""

import logging
from django.conf import settings
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

logger = logging.getLogger(__name__)

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
    view = context.get("view")
    view_name = view.__class__.__name__ if view else "UnknownView"
    request = context.get("request")
    endpoint = f"{request.method} {request.path}" if request else "UnknownEndpoint"

    # 1. Domain exceptions raised by your application/domain/adapters
    if isinstance(exc, DomainError):
        http_status = _status_for(exc)
        log_fn = logger.error if http_status >= 500 else logger.warning
        log_fn(
            "[%s] %s | DomainError [%s]: %s | details=%s",
            endpoint,
            view_name,
            exc.code,
            exc.message,
            exc.details,
            exc_info=settings.DEBUG,  # Shows exact `raise` file & line in dev console
        )
        return Response(
            {"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
            status=http_status,
        )

    # 2. DRF built-in exceptions (serializer validation, auth, permissions, 404, throttle)
    response = drf_default_handler(exc, context)
    if response is not None:
        code = getattr(exc, "default_code", "error")
        message = _message(response.data)
        logger.warning(
            "[%s] %s | DRF (%s) [%s]: %s",
            endpoint,
            view_name,
            response.status_code,
            code,
            message,
        )
        response.data = {"error": {"code": code, "message": message, "details": {}}}
        return response

    # 3. Unexpected 500 crashes (unhandled Python/DB exceptions)
    logger.exception("[%s] %s | Unhandled internal server error", endpoint, view_name)
    return None


def _message(data) -> str:
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            return str(detail)
        return "; ".join(f"{k}: {v}" for k, v in data.items())
    if isinstance(data, list):
        return "; ".join(str(x) for x in data)
    return str(data)