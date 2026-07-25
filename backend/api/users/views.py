"""Public user profiles and a user's public reports. AllowAny — world-readable, no PII."""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import paginated_response
from api.reports.serializers import PublicPostSerializer
from api.reports.views import _like_context
from api.users.serializers import PublicProfileSerializer
from config import container
from core.application.accounts.public_profile import GetPublicProfile
from core.application.reports.queries import ListUserReports
from core.domain.ids import UserId
from core.domain.pagination import PageRequest

PROFILE_POSTS_PER_PAGE = 5


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id: int):
        user, contribution, badges = GetPublicProfile(
            container.users(),
            container.leaderboard(),
            container.point_rules(),
            container.level_rules(),
            container.badges(),
        ).execute(UserId(user_id))
        return Response(
            PublicProfileSerializer(
                user, context={"contribution": contribution, "badges": badges}
            ).data
        )


class UserPostsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id: int):
        page = ListUserReports(container.posts()).execute(
            UserId(user_id),
            PageRequest(
                limit=PROFILE_POSTS_PER_PAGE, cursor=request.query_params.get("cursor") or None
            ),
        )
        return paginated_response(page, PublicPostSerializer, _like_context(request, page.items))
