from rest_framework import serializers

from config import container
from core.domain.entities import User
from core.domain.value_objects import Role


class ModerateSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class AdminUserSerializer(serializers.Serializer):
    """Full user row for staff/admin - no password, but role and active state included."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    role = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()
    is_active = serializers.BooleanField()
    avatar_url = serializers.SerializerMethodField()

    def get_role(self, user: User) -> str:
        return user.role.value

    def get_avatar_url(self, user: User) -> str | None:
        return container.image_storage().public_url(user.avatar) if user.avatar else None


class AdminUserDetailSerializer(AdminUserSerializer):
    """User row + all-time contribution stats. Pass the Contribution via serializer context."""

    posts_approved = serializers.SerializerMethodField()
    likes_received = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    def get_posts_approved(self, user: User) -> int:
        return self.context["contribution"].posts_approved

    def get_likes_received(self, user: User) -> int:
        return self.context["contribution"].likes_received

    def get_total_points(self, user: User) -> int:
        return self.context["contribution"].total_points


class AuditLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    admin = serializers.CharField(source="admin_name")
    action = serializers.CharField()
    post_id = serializers.IntegerField()
    reason = serializers.CharField()
    at = serializers.DateTimeField()


class AdminMapMarkerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    severity = serializers.IntegerField()
    status = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    def get_status(self, marker) -> int:
        return int(marker.status)

    def get_image_url(self, marker) -> str:
        if getattr(marker, "image", None):
            return container.image_storage().public_url(marker.image)
        return ""


class SetActiveSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class SetRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[r.value for r in Role])


class StatsSerializer(serializers.Serializer):
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    hidden = serializers.IntegerField()
    rejected = serializers.IntegerField()
    total = serializers.IntegerField()


class WeeklyPointSerializer(serializers.Serializer):
    week = serializers.DateField()
    submitted = serializers.IntegerField()
    approved = serializers.IntegerField()


class AnalyticsSerializer(serializers.Serializer):
    over_time = WeeklyPointSerializer(many=True)
    active_users = serializers.IntegerField()
