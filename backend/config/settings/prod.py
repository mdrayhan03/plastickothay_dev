"""Production settings.

Same-origin deployment: Django serves the React build via Whitenoise, so the httpOnly refresh
cookie stays first-party and CORS is not needed (LLD §11.2, DEC-7).
"""

import os

from config.settings.base import *  # noqa: F401,F403
from config.settings.base import FRONTEND_DIST, INSTALLED_APPS

DEBUG = False

# Whitenoise serves the built SPA (frontend/dist) at the site root - so /assets/*.js, the
# manifest, the service worker and icons are served as real files, while any non-file route
# falls through to Django's catch-all (config/urls.py) which returns index.html for client-side
# routing. Same-origin, no CORS (DEC-7). Requires `npm run build` before deploy.
if FRONTEND_DIST.exists():
    WHITENOISE_ROOT = str(FRONTEND_DIST)

# Mailjet transport (anymail) is only needed in prod - dev/test use console/locmem backends,
# so it stays out of the base INSTALLED_APPS and its install is a prod-only dependency.
INSTALLED_APPS = [*INSTALLED_APPS, "anymail"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "anymail.backends.mailjet.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
ANYMAIL = {
    "MAILJET_API_KEY": os.getenv("MAILJET_API_KEY", ""),
    "MAILJET_SECRET_KEY": os.getenv("MAILJET_SECRET_KEY", ""),
    # (connect, read) seconds - a slow Mailjet must not hang the request.
    "REQUESTS_TIMEOUT": (5, 10),
}
