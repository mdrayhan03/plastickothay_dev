"""Root URL configuration.

API routes are wired from B2 onward. Django admin is mounted for config-table CRUD only
(LLD §11.4); a catch-all serving the SPA index is added at B7.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # path("api/", include("api.urls")),   # B2+
]
