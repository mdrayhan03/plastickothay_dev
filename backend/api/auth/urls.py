from django.urls import path

from api.auth import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("verify/", views.VerifyOTPView.as_view(), name="verify"),
    path("resend-otp/", views.ResendOTPView.as_view(), name="resend-otp"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.RefreshView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset-password"),
]
