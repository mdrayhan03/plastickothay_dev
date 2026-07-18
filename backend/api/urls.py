from django.urls import include, path

from api.auth.views import MeView

urlpatterns = [
    path("auth/", include("api.auth.urls")),
    path("me/", MeView.as_view(), name="me"),
    path("", include("api.reports.urls")),
    path("admin/", include("api.admin.urls")),
    # engagement, scoring, content wired in B5–B6
]
