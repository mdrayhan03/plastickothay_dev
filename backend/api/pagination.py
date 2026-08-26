"""Cursor pagination bridge.

The repositories already do keyset pagination over (created DESC, id DESC) and return a
domain Page with a next_cursor. This helper just renders that into a consistent JSON envelope;
it is not a DRF paginator (use cases return domain Pages, not querysets).
"""

from rest_framework.response import Response

from core.domain.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page, PageRequest


def page_request(request) -> PageRequest:
    try:
        limit = int(request.query_params.get("limit", DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        limit = DEFAULT_PAGE_SIZE
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    cursor = request.query_params.get("cursor") or None
    return PageRequest(limit=limit, cursor=cursor)


def paginated_response(page: Page, serializer_cls, context=None) -> Response:
    return Response(
        {
            "results": serializer_cls(page.items, many=True, context=context or {}).data,
            "next_cursor": page.next_cursor,
        }
    )
