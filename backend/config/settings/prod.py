"""Production settings.

Same-origin deployment: Django serves the React build via Whitenoise, so the httpOnly refresh
cookie stays first-party and CORS is not needed (LLD §11.2, DEC-7).
"""

import os

from config.settings.base import *  # noqa: F401,F403

DEBUG = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "anymail.backends.mailjet.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
ANYMAIL = {
    "MAILJET_API_KEY": os.getenv("MAILJET_API_KEY", ""),
    "MAILJET_SECRET_KEY": os.getenv("MAILJET_SECRET_KEY", ""),
}
