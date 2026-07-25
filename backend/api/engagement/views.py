"""Like / unlike endpoints.

Liking is open to anyone (AllowAny) — anonymous likes are recorded and counted but award
nobody (DEC-1, enforced in the domain). Unliking requires auth (an anonymous caller has no
identity to match). Both are throttled.
"""

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api.authentication import actor_id
from config import container
from core.application.engagement.likes import LikePost, UnlikePost


class LikeView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "POST" else [IsAuthenticated()]

    def get_throttles(self):
        throttle = ScopedRateThrottle()
        # Different bucket for anonymous vs authenticated likers.
        self.throttle_scope = "auth_like" if actor_id(self.request) else "anon_like"
        return [throttle]

    def post(self, request, post_id: int):
        result = LikePost(
            container.posts(), container.engagements(), container.unit_of_work(), container.clock()
        ).execute(post_id, actor_id(request))
        return Response(
            {"post_id": result.post_id, "likes": result.likes, "liked_by_me": result.liked_by_me},
            status=201,
        )

    def delete(self, request, post_id: int):
        result = UnlikePost(
            container.posts(), container.engagements(), container.unit_of_work()
        ).execute(post_id, actor_id(request))
        return Response(
            {"post_id": result.post_id, "likes": result.likes, "liked_by_me": result.liked_by_me}
        )
