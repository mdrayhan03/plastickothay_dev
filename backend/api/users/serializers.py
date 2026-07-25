"""Public user-profile serialization. No email/phone — this is world-readable."""

from rest_framework import serializers

from config import container
from core.domain.entities import User


class PublicBadgeSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    icon = serializers.CharField()


class PublicProfileSerializer(serializers.Serializer):
    """Serializes a User; the Contribution and earned badges come from serializer context."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    level_title = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    posts_approved = serializers.SerializerMethodField()
    likes_received = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()

    def get_full_name(self, user: User) -> str:
        return user.full_name

    def get_avatar_url(self, user: User) -> str | None:
        return container.image_storage().public_url(user.avatar) if user.avatar else None

    def get_level(self, user: User) -> int:
        return self.context["contribution"].level

    def get_level_title(self, user: User) -> str:
        return self.context["contribution"].level_title

    def get_total_points(self, user: User) -> int:
        return self.context["contribution"].total_points

    def get_posts_approved(self, user: User) -> int:
        return self.context["contribution"].posts_approved

    def get_likes_received(self, user: User) -> int:
        return self.context["contribution"].likes_received

    def get_badges(self, user: User) -> list:
        return PublicBadgeSerializer(self.context["badges"], many=True).data
