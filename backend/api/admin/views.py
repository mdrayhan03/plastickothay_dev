"""Admin moderation API - staff/admin only.

Every route is IsStaffOrAdmin. AdminPostSerializer is used here (the only place reporter
email/phone are exposed). No point logic anywhere - points derive from status (DEC-2).
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from api.admin.serializers import (
    AdminMapMarkerSerializer,
    AdminUserDetailSerializer,
    AdminUserSerializer,
    AnalyticsSerializer,
    AuditLogSerializer,
    ModerateSerializer,
    SetActiveSerializer,
    SetRoleSerializer,
    StatsSerializer,
)
from api.authentication import actor_id
from api.pagination import page_request, paginated_response
from api.permissions import IsAdmin, IsStaffOrAdmin
from api.reports.serializers import AdminPostSerializer
from config import container
from core.application.accounts.administration import (
    DeleteUser,
    GetUserDetail,
    ListUsers,
    SetUserActive,
    SetUserRole,
)
from core.application.reports.dto import ModerateCommand
from core.application.reports.moderation import (
    ApproveReport,
    GetPostAnalytics,
    GetPostStats,
    HideReport,
    ListAuditLog,
    ListReportsForReview,
    RejectReport,
    UnhideReport,
)
from core.application.reports.queries import ListAdminMapMarkers
from core.domain.ids import UserId
from core.domain.value_objects import PostStatus, Role

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
        user_id = request.query_params.get("user_id")
        names = request.query_params.getlist("status")
        if not names:
            names = ["pending", "approved", "hidden", "rejected"] if user_id else ["pending"]
        statuses = tuple(_STATUS_BY_NAME[n] for n in names if n in _STATUS_BY_NAME)
        severity = request.query_params.get("severity")
        page = ListReportsForReview(container.posts()).execute(
            page_request(request),
            statuses=statuses
            or (PostStatus.PENDING, PostStatus.APPROVED, PostStatus.HIDDEN, PostStatus.REJECTED),
            severity=int(severity) if severity else None,
            include_deleted="rejected" in names or user_id is not None,
            reporter_id=UserId(int(user_id)) if user_id else None,
        )
        return paginated_response(page, AdminPostSerializer)


class ApproveView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = ApproveReport(
            container.posts(),
            container.moderation_log(),
            container.notifier(),
            container.unit_of_work(),
            container.clock(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class RejectView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = RejectReport(
            container.posts(),
            container.moderation_log(),
            container.notifier(),
            container.unit_of_work(),
            container.clock(),
            container.image_storage(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class HideView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = HideReport(
            container.posts(),
            container.moderation_log(),
            container.notifier(),
            container.unit_of_work(),
            container.clock(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class UnhideView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, post_id: int):
        post = UnhideReport(
            container.posts(),
            container.moderation_log(),
            container.notifier(),
            container.unit_of_work(),
            container.clock(),
        ).execute(_cmd(request, post_id))
        return Response(AdminPostSerializer(post).data)


class StatsView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        counts = GetPostStats(container.posts()).execute()
        return Response(
            StatsSerializer(
                {
                    "pending": counts.get(PostStatus.PENDING),
                    "approved": counts.get(PostStatus.APPROVED),
                    "hidden": counts.get(PostStatus.HIDDEN),
                    "rejected": counts.get(PostStatus.REJECTED),
                    "total": counts.total,
                }
            ).data
        )


class AuditLogView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        page = ListAuditLog(container.moderation_log(), container.users()).execute(
            page_request(request)
        )
        return paginated_response(page, AuditLogSerializer)


class AdminMapView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        markers = ListAdminMapMarkers(container.posts()).execute()
        return Response(AdminMapMarkerSerializer(markers, many=True).data)


class AnalyticsView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        analytics = GetPostAnalytics(container.posts(), container.clock()).execute()
        return Response(AnalyticsSerializer(analytics).data)


class UserListView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        page = ListUsers(container.users()).execute(page_request(request))
        return paginated_response(page, AdminUserSerializer)


class UserActiveView(APIView):
    """Activate / deactivate a user. Staff or admin; the use case forbids self and,
    for staff, deactivating an admin."""

    permission_classes = [IsStaffOrAdmin]

    def patch(self, request, user_id: int):
        s = SetActiveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = SetUserActive(container.users(), container.unit_of_work()).execute(
            UserId(user_id), s.validated_data["is_active"], actor_id(request)
        )
        return Response(AdminUserSerializer(user).data)


class UserRoleView(APIView):
    """Change a user's role. Admin (superuser) only - enforced here and in the use case."""

    permission_classes = [IsAdmin]

    def patch(self, request, user_id: int):
        s = SetRoleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = SetUserRole(container.users(), container.unit_of_work()).execute(
            UserId(user_id), Role(s.validated_data["role"]), actor_id(request)
        )
        return Response(AdminUserSerializer(user).data)


class UserDetailView(APIView):
    """A single user with contribution stats (staff), and delete (admin, inactive-only)."""

    def get_permissions(self):
        return [IsAdmin()] if self.request.method == "DELETE" else [IsStaffOrAdmin()]

    def get(self, request, user_id: int):
        user, contribution = GetUserDetail(
            container.users(),
            container.leaderboard(),
            container.point_rules(),
            container.level_rules(),
        ).execute(UserId(user_id))
        return Response(
            AdminUserDetailSerializer(user, context={"contribution": contribution}).data
        )

    def delete(self, request, user_id: int):
        DeleteUser(container.users(), container.unit_of_work()).execute(
            UserId(user_id), actor_id(request)
        )
        return Response(status=204)
