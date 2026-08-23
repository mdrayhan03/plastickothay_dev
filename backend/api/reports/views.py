"""Reports API - public reads and open submission.

Public list/detail pin status to APPROVED in the use case, never via a query param. Public
serializers never expose reporter email/phone (LLD §8.3). Submission is open to anyone
(anonymous or authenticated), throttled for anonymous callers.
"""

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api.authentication import actor_id
from api.pagination import page_request, paginated_response
from api.reports.serializers import (
    MapMarkerSerializer,
    OwnPostSerializer,
    PublicPostSerializer,
    SubmitReportSerializer,
    UpdateDescriptionSerializer,
)
from config import container
from core.application.reports.dto import SubmitReportCommand, UpdateDescriptionCommand
from core.application.reports.queries import (
    GetReport,
    ListMapMarkers,
    ListOwnReports,
    ListReports,
    UpdateReportDescription,
)
from core.application.reports.submission import SubmitReport
from core.domain.value_objects import EngagementType


def _like_context(request, posts) -> dict:
    """Batch the like count and the caller's like state for a page of posts (avoids N+1)."""
    ids = [p.id for p in posts if p.id is not None]
    if not ids:
        return {"likes": {}, "liked_ids": set()}
    engagements = container.engagements()
    counts = engagements.counts_for(ids, EngagementType.LIKE)
    actor = actor_id(request)
    liked = engagements.liked_post_ids(ids, actor) if actor else set()
    return {"likes": counts, "liked_ids": liked}


class ReportListCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "anon_post_submit"

    def get_throttles(self):
        # Only throttle submission, not reads.
        return [ScopedRateThrottle()] if self.request.method == "POST" else []

    def get(self, request):
        try:
            severity = request.query_params.get("severity")
            severity = int(severity) if severity else None
        except ValueError:
            severity = None
        page = ListReports(container.posts()).execute(page_request(request), severity=severity)
        return paginated_response(page, PublicPostSerializer, _like_context(request, page.items))

    def post(self, request):
        s = SubmitReportSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        cmd = SubmitReportCommand(
            severity=d["severity"],
            lat=d["lat"],
            lon=d["lon"],
            photo_bytes=d["photo_bytes"],
            filename=d["filename"],
            content_type=d["content_type"],
            place_name=d["place_name"],
            description=d["description"],
            name=d["name"],
            email=d["email"],
            phone=d["phone"],
        )
        post = SubmitReport(
            container.posts(),
            container.users(),
            container.image_storage(),
            container.unit_of_work(),
            container.clock(),
        ).execute(cmd, actor_id(request))
        return Response(PublicPostSerializer(post).data, status=201)


class ReportDetailView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    def get(self, request, post_id: int):
        post = GetReport(container.posts()).execute(post_id)
        return Response(PublicPostSerializer(post, context=_like_context(request, [post])).data)

    def patch(self, request, post_id: int):
        s = UpdateDescriptionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        post = UpdateReportDescription(container.posts(), container.unit_of_work()).execute(
            UpdateDescriptionCommand(
                post_id=post_id,
                description=s.validated_data["description"],
                actor_id=actor_id(request),
            )
        )
        return Response(OwnPostSerializer(post).data)


class MapView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        markers = ListMapMarkers(container.posts()).execute()
        return Response(MapMarkerSerializer(markers, many=True).data)


class OwnReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = ListOwnReports(container.posts()).execute(actor_id(request), page_request(request))
        return paginated_response(page, OwnPostSerializer, _like_context(request, page.items))
