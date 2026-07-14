from django.urls import path
from . import views

app_name = "plastickothay"
urlpatterns = [
    path("", views.home, name="home"),
    path("posts/", views.posts, name="posts"),
    path("post/<str:id>/", views.post, name="post"),
    path("contact/", views.contact, name="contact"),
    path("rate-us/", views.feedback, name="feedback"),
    path("contribution/", views.contribution, name="contribution"),
    path("keep-alive/", views.keep_alive, name="keep_alive"),
]