"""Auth API views — thin: validate → use case → serialize.

No business logic here. Domain errors propagate to the exception handler (LLD §8.5).
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from adapters.notifications.mailjet import MailjetNotifier
from adapters.security.jwt_service import SimpleJWTTokenService
from api.auth.serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    UpdateProfileSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
from api.authentication import actor_id
from api.cookies import clear_refresh_cookie, read_refresh_cookie, set_refresh_cookie
from config import container
from core.application.accounts.authentication import Login, Logout, RefreshToken
from core.application.accounts.dto import (
    LoginCommand,
    RegisterCommand,
    ResetPasswordCommand,
    UpdateProfileCommand,
    VerifyOTPCommand,
)
from core.application.accounts.password import RequestPasswordReset, ResetPassword
from core.application.accounts.profile import GetProfile, UpdateProfile
from core.application.accounts.registration import RegisterUser, ResendOTP, VerifyOTP
from core.domain.errors import InvalidToken
from core.domain.value_objects import OTPPurpose


def _tokens():
    return SimpleJWTTokenService()


def _validated(serializer_cls, request):
    s = serializer_cls(data=request.data)
    s.is_valid(raise_exception=True)
    return s.validated_data


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = _validated(RegisterSerializer, request)
        use_case = RegisterUser(
            container.users(),
            container.otps(),
            MailjetNotifier(),
            container.unit_of_work(),
            container.clock(),
            container.image_storage(),
        )
        use_case.execute(RegisterCommand(**data))
        return Response(
            {"detail": "Registered. Check your email for a verification code."},
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = _validated(VerifyOTPSerializer, request)
        VerifyOTP(
            container.users(), container.otps(), container.unit_of_work(), container.clock()
        ).execute(VerifyOTPCommand(**data))
        return Response({"detail": "Account verified. You can now sign in."})


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_resend"  # 3/hour — OTP emails cost money and enable spam

    def post(self, request):
        data = _validated(ResendOTPSerializer, request)
        ResendOTP(
            container.users(), container.otps(), MailjetNotifier(), container.clock()
        ).execute(data["username"], OTPPurpose.REGISTRATION)
        return Response({"detail": "If the account exists, a new code has been sent."})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"  # 10/hour/IP — blunts credential stuffing

    def post(self, request):
        data = _validated(LoginSerializer, request)
        user, pair = Login(container.users(), _tokens(), container.clock()).execute(
            LoginCommand(**data)
        )
        response = Response({"access": pair.access, "user": UserSerializer(user).data})
        return set_refresh_cookie(response, pair.refresh)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = read_refresh_cookie(request)
        if not token:
            raise InvalidToken("No refresh token.")
        pair = RefreshToken(container.users(), _tokens()).execute(token)
        response = Response({"access": pair.access})
        return set_refresh_cookie(response, pair.refresh)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Logout(_tokens()).execute(read_refresh_cookie(request))
        response = Response({"detail": "Logged out."})
        return clear_refresh_cookie(response)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = _validated(ForgotPasswordSerializer, request)
        RequestPasswordReset(
            container.users(), container.otps(), MailjetNotifier(), container.clock()
        ).execute(data["username"])
        return Response({"detail": "If the account exists, a reset code has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = _validated(ResetPasswordSerializer, request)
        ResetPassword(
            container.users(),
            container.otps(),
            _tokens(),
            container.unit_of_work(),
            container.clock(),
        ).execute(ResetPasswordCommand(**data))
        return Response({"detail": "Password reset. You can now sign in."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = GetProfile(container.users()).execute(actor_id(request))
        return Response(UserSerializer(user).data)

    def patch(self, request):
        data = _validated(UpdateProfileSerializer, request)
        user = UpdateProfile(
            container.users(), container.unit_of_work(), container.image_storage()
        ).execute(UpdateProfileCommand(**data), actor_id(request))
        return Response(UserSerializer(user).data)
