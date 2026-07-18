from django.urls import path

from api.reports import views

urlpatterns = [
    path("posts/", views.ReportListCreateView.as_view(), name="report-list"),
    path("posts/<int:post_id>/", views.ReportDetailView.as_view(), name="report-detail"),
    path("map/posts/", views.MapView.as_view(), name="report-map"),
    path("me/posts/", views.OwnReportsView.as_view(), name="own-reports"),
]
