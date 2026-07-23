"""SPA index view.

Serves the built React app's index.html for any non-API route. Until the frontend is built
(frontend/dist/index.html), returns a friendly placeholder so the backend runs standalone.
"""

from django.conf import settings
from django.http import HttpResponse
from django.views import View

_PLACEHOLDER = (
    "<!doctype html><meta charset='utf-8'><title>PlasticKothay API</title>"
    "<body style='font-family:sans-serif;max-width:40rem;margin:4rem auto'>"
    "<h1>PlasticKothay backend is running</h1>"
    "<p>The React app has not been built yet. The API is live under "
    "<code>/api/</code>.</p></body>"
)


class SPAView(View):
    def get(self, request, *args, **kwargs):
        index = settings.FRONTEND_DIST / "index.html"
        if index.exists():
            return HttpResponse(index.read_text(encoding="utf-8"))
        return HttpResponse(_PLACEHOLDER)
