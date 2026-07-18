from django.urls import path

from api.engagement.views import LikeView

urlpatterns = [
    path("posts/<int:post_id>/like/", LikeView.as_view(), name="like"),
]
