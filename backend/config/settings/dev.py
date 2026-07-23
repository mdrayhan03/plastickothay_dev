"""Development settings."""

from config.settings.base import *  # noqa: F401,F403

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Skip createcachetable locally; prod uses the shared DatabaseCache from base.py.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
