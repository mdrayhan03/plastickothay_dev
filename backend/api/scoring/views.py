"""Leaderboard and contribution endpoints."""

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.authentication import actor_id
from api.pagination import page_request
from config import container
from core.application.scoring.leaderboard import GetContribution, GetLeaderboard
from core.domain.value_objects import Period


class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        raw = request.query_params.get("period", "all")
        try:
            period = Period(raw)
        except ValueError:
            period = Period.ALL
        page = GetLeaderboard(container.leaderboard(), container.point_rules()).execute(
            period, page_request(request)
        )
        results = [
            {"rank": r.rank, "user_id": r.user_id, "username": r.username,
             "full_name": r.full_name, "points": r.points}
            for r in page.items
        ]
        return Response({"period": period.value, "results": results,
                         "next_cursor": page.next_cursor})


class ContributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        c = GetContribution(
            container.leaderboard(), container.point_rules(), container.level_rules()
        ).execute(actor_id(request))
        return Response({
            "total_points": c.total_points,
            "posts_approved": c.posts_approved,
            "likes_received": c.likes_received,
            "likes_given": c.likes_given,
            "level": c.level,
            "level_title": c.level_title,
            "points_to_next_level": c.points_to_next_level,
            "progress_percentage": c.progress_percentage,
            "referrals": c.referrals,
        })
