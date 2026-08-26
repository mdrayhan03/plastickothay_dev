from django.urls import path

from api.users import views

urlpatterns = [
    path("users/<int:user_id>/", views.PublicProfileView.as_view(), name="public-profile"),
    path("users/<int:user_id>/posts/", views.UserPostsView.as_view(), name="user-posts"),
]
