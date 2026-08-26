"""Root URL configuration.

Order matters: /api and /django-admin are matched first; everything else falls through to the
SPA catch-all, which returns the React index.html so client-side routes survive a hard refresh.
Serving the SPA from Django keeps it same-origin with the API (DEC-7) - the httpOnly refresh
cookie stays first-party and CORS is unnecessary in production.
"""

from django.contrib import admin
from django.urls import include, path, re_path

from config.spa import SPAView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("api.urls")),
    # Catch-all - must be last. Excludes /api and /django-admin (matched above).
    re_path(r"^(?!api/|django-admin/).*$", SPAView.as_view(), name="spa"),
]
