"""Report serializers — the public/admin split (LLD §8.3).

This is where the legacy PII leak is closed. The public serializers expose reporter NAME only;
email and phone are reachable exclusively through the admin serializer, behind an admin token.
Base64 photo decoding happens here (transport concern), never in a use case.
"""

import base64

from rest_framework import serializers

from config import container
from core.domain.entities import Post


def _image_url(post: Post) -> str:
    return container.image_storage().public_url(post.image)


class SubmitReportSerializer(serializers.Serializer):
    """Accepts a report from anyone. Contact fields are used only for anonymous callers;
    for authenticated callers the use case ignores them and uses the stored profile."""

    severity = serializers.IntegerField(min_value=1, max_value=5)
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    photo = serializers.CharField()  # base64 data URL
    description = serializers.CharField(required=False, allow_blank=True, default="")
    name = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        raw = attrs["photo"]
        if ";base64," in raw:
            header, b64 = raw.split(";base64,", 1)
            content_type = header.split(":")[-1] or "image/jpeg"
        else:
            b64, content_type = raw, "image/jpeg"
        try:
            attrs["photo_bytes"] = base64.b64decode(b64, validate=True)
        except Exception as exc:
            raise serializers.ValidationError({"photo": "Invalid base64 image."}) from exc
        attrs["content_type"] = content_type
        ext = content_type.split("/")[-1] or "jpg"
        attrs["filename"] = f"upload.{ext}"
        return attrs


class PublicPostSerializer(serializers.Serializer):
    """No email, no phone. Reporter name only."""

    id = serializers.IntegerField()
    reporter_name = serializers.SerializerMethodField()
    severity = serializers.IntegerField()
    image_url = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    description = serializers.CharField()
    created = serializers.DateTimeField()

    def get_reporter_name(self, post: Post) -> str:
        return post.reporter.name

    def get_image_url(self, post: Post) -> str:
        return _image_url(post)

    def get_lat(self, post: Post) -> float:
        return post.location.lat

    def get_lon(self, post: Post) -> float:
        return post.location.lon


class OwnPostSerializer(PublicPostSerializer):
    """The reporter's own posts — adds status so they can see pending/hidden state."""

    status = serializers.SerializerMethodField()

    def get_status(self, post: Post) -> int:
        return int(post.status)


class MapMarkerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    severity = serializers.IntegerField()


class AdminPostSerializer(serializers.Serializer):
    """Admin-only — the ONLY place reporter email/phone are exposed."""

    id = serializers.IntegerField()
    reporter_name = serializers.SerializerMethodField()
    reporter_email = serializers.SerializerMethodField()
    reporter_phone = serializers.SerializerMethodField()
    reporter_id = serializers.IntegerField(allow_null=True)
    severity = serializers.IntegerField()
    image_url = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    description = serializers.CharField()
    status = serializers.SerializerMethodField()
    created = serializers.DateTimeField()
    approved_at = serializers.DateTimeField(allow_null=True)

    def get_reporter_name(self, post: Post) -> str:
        return post.reporter.name

    def get_reporter_email(self, post: Post) -> str:
        return post.reporter.email

    def get_reporter_phone(self, post: Post) -> str:
        return post.reporter.phone

    def get_image_url(self, post: Post) -> str:
        return _image_url(post)

    def get_lat(self, post: Post) -> float:
        return post.location.lat

    def get_lon(self, post: Post) -> float:
        return post.location.lon

    def get_status(self, post: Post) -> int:
        return int(post.status)


class UpdateDescriptionSerializer(serializers.Serializer):
    description = serializers.CharField(allow_blank=True)
