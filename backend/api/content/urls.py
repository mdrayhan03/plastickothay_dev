from django.urls import path

from api.content import views

urlpatterns = [
    path("contact-page/", views.ContactPageView.as_view(), name="contact-page"),
    path("contact-messages/", views.ContactMessageView.as_view(), name="contact-messages"),
    path(
        "contact-messages/<int:message_id>/",
        views.ContactMessageStatusView.as_view(),
        name="contact-message-status",
    ),
    path("feedback/", views.FeedbackView.as_view(), name="feedback"),
    path("site-config/", views.SiteConfigView.as_view(), name="site-config"),
]
