"""Root URL configuration.

Order matters: /api, /django-admin, and /media are matched first; everything else falls through to the
SPA catch-all, which returns the React index.html so client-side routes survive a hard refresh.
Serving the SPA from Django keeps it same-origin with the API (DEC-7) - the httpOnly refresh
cookie stays first-party and CORS is unnecessary in production.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from config.spa import SPAView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all - must be last. Excludes /api, /django-admin, and /media (matched above).
urlpatterns += [
    re_path(r"^(?!api/|django-admin/|media/).*$", SPAView.as_view(), name="spa"),
]

