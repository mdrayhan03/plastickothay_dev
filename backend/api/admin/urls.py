from django.urls import path

from api.admin import views

urlpatterns = [
    path("posts/", views.ReviewListView.as_view(), name="admin-review-list"),
    path("posts/<int:post_id>/approve/", views.ApproveView.as_view(), name="admin-approve"),
    path("posts/<int:post_id>/reject/", views.RejectView.as_view(), name="admin-reject"),
    path("posts/<int:post_id>/hide/", views.HideView.as_view(), name="admin-hide"),
    path("posts/<int:post_id>/unhide/", views.UnhideView.as_view(), name="admin-unhide"),
    path("stats/", views.StatsView.as_view(), name="admin-stats"),
    path("audit/", views.AuditLogView.as_view(), name="admin-audit"),
    path("map/", views.AdminMapView.as_view(), name="admin-map"),
    path("analytics/", views.AnalyticsView.as_view(), name="admin-analytics"),
    path("users/", views.UserListView.as_view(), name="admin-user-list"),
    path("users/<int:user_id>/", views.UserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:user_id>/active/", views.UserActiveView.as_view(), name="admin-user-active"),
    path("users/<int:user_id>/role/", views.UserRoleView.as_view(), name="admin-user-role"),
]
