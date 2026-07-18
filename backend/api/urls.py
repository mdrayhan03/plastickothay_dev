from django.urls import include, path

from api.auth.views import MeView

urlpatterns = [
    path("auth/", include("api.auth.urls")),
    path("me/", MeView.as_view(), name="me"),
    # reports, engagement, scoring, admin, content wired in B3–B6
]
