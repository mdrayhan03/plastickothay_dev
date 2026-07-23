"""Admin moderation API — staff/admin only.

Every route is IsStaffOrAdmin. AdminPostSerializer is used here (the only place reporter
email/phone are exposed). No point logic anywhere — points derive from status (DEC-2).
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from api.admin.serializers import ModerateSerializer, StatsSerializer
from api.authentication import actor_id
from api.pagination import page_request, paginated_response
from api.permissions import IsStaffOrAdmin
from api.reports.serializers import AdminPostSerializer
from config import container
from core.application.reports.dto import ModerateCommand
from core.application.reports.moderation import (
    ApproveReport,
    GetPostStats,
    HideReport,
    ListReportsForReview,
    RejectReport,
    UnhideReport,
)
from core.domain.value_objects import PostStatus

_STATUS_BY_NAME = {
    "pending": PostStatus.PENDING,
    "approved": PostStatus.APPROVED,
    "hidden": PostStatus.HIDDEN,
    "rejected": PostStatus.REJECTED,
}


def _cmd(request, post_id: int) -> ModerateCommand:
    s = ModerateSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    return ModerateCommand(
        post_id=post_id, admin_id=actor_id(request), reason=s.validated_data["reason"]
    )


class ReviewListView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        names = request.query_params.getlist("status") or ["pending"]
        statuses = tuple(_STATUS_BY_NAME[n] for n in names if n in _STATUS_BY_NAME)
        severity = request.query_params.get("severity")
        page = ListReportsForReview(container.posts()).execute(
            page_request(request),
            statuses=statuses or (PostStatus.PENDING,),
            severity=int(severity) if severity else None,
            include_deleted="rejected" in names,
        )
        return paginated_response(page, AdminPostSerializer)


class ApproveView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = ApproveReport(
            container.posts(), container.moderation_log(), container.notifier(),
            container.unit_of_work(), container.clock(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class RejectView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = RejectReport(
            container.posts(), container.moderation_log(), container.notifier(),
            container.unit_of_work(), container.clock(), container.image_storage(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class HideView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = HideReport(
            container.posts(), container.moderation_log(), container.notifier(),
            container.unit_of_work(), container.clock(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class UnhideView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = UnhideReport(
            container.posts(), container.moderation_log(), container.notifier(),
            container.unit_of_work(), container.clock(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class StatsView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        counts = GetPostStats(container.posts()).execute()
        return Response(
            StatsSerializer({
                "pending": counts.get(PostStatus.PENDING),
                "approved": counts.get(PostStatus.APPROVED),
                "hidden": counts.get(PostStatus.HIDDEN),
                "rejected": counts.get(PostStatus.REJECTED),
                "total": counts.total,
            }).data
        )
