"""Auth request/response serializers.

These validate transport shape and translate to/from use-case commands and domain entities.
They never touch the ORM.
"""

from rest_framework import serializers

from core.domain.entities import User


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(min_length=8, write_only=True)


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

    def get_role(self, user: User) -> str:
        return user.role.value


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=20, required=False)
