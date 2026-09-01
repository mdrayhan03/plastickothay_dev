"""Auth request/response serializers.

These validate transport shape and translate to/from use-case commands and domain entities.
They never touch the ORM.
"""

import base64

from rest_framework import serializers

from api.reports.serializers import decode_base64_image
from config import container
from core.application.accounts.dto import Avatar
from core.domain.entities import User


def _decode_avatar(raw: str) -> Avatar | None:
    """Turn an optional base64 data URL into an Avatar command object (or None)."""
    if not raw:
        return None
    try:
        data, content_type = decode_base64_image(raw)
    except Exception as exc:
        raise serializers.ValidationError({"avatar": "Invalid base64 image."}) from exc
    ext = content_type.split("/")[-1].split("+")[0] or "jpg"
    return Avatar(data=data, filename=f"avatar.{ext}", content_type=content_type)


def _avatar_url(user: User) -> str | None:
    return container.image_storage().public_url(user.avatar) if user.avatar else None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(min_length=8, write_only=True)
    avatar = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        attrs["avatar"] = _decode_avatar(attrs.get("avatar") or "")
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    username = serializers.CharField()
    code = serializers.IntegerField()


class ResendOTPSerializer(serializers.Serializer):
    username = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    code = serializers.IntegerField()
    new_password = serializers.CharField(min_length=8, write_only=True)


class UserSerializer(serializers.Serializer):
    """Public shape of the authenticated user's own profile."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    role = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()
    avatar_url = serializers.SerializerMethodField()

    def get_role(self, user: User) -> str:
        return user.role.value

    def get_avatar_url(self, user: User) -> str | None:
        return _avatar_url(user)


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    avatar = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        if "avatar" in attrs:
            attrs["avatar"] = _decode_avatar(attrs.get("avatar") or "")
        return attrs
