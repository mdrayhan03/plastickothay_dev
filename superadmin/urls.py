from django.urls import path
from . import views

app_name = "superadmin"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("verification/<str:username>", views.account_verification, name="verification"),
    path("forgetpassword/", views.forget_password, name="forgetpassword"),
    path("passwordverification/<str:username>", views.password_verification, name="passwordverification"),
    path("resetpassword/<str:username>", views.reset_password, name="resetpassword"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("unauthorized/", views.unauthorized_view, name="unauthorized"),
    path("api/dashboard/", views.dashboard_stats_api, name="dashboard_stats_api"),
    path("api/accept/<str:id>/", views.api_accept_post, name="api_accept_post"),
    path("api/reject/<str:id>/", views.api_reject_post, name="api_reject_post"),
    path("accept/<str:id>", views.accept_post, name="accept"),
    path("reject/<str:id>", views.reject_post, name="reject"),
    path("users/", views.users_view, name="users"),
    path("user/", views.user_view, name="user"),
    path("logout/", views.logout_view, name="logout"),
]