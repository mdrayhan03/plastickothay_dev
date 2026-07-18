from django.urls import path

from api.scoring.views import ContributionView, LeaderboardView

urlpatterns = [
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("me/contribution/", ContributionView.as_view(), name="contribution"),
]
