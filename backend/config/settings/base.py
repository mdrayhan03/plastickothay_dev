"""Base settings shared by every environment.

Database selection is driven by the MODE env var (DEV | PROD | TEST). Only PROD uses the real
Postgres (DATABASE_URL); DEV and TEST use local SQLite even if DATABASE_URL is set, so local and
test runs can never touch the production database. Engine choice is a settings value, not a
hand-rolled factory - Django already gives that for free (LLD §1.1, discussion).
"""

import os
from pathlib import Path

# pyrefly: ignore [missing-import]
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_KEY", "dev-insecure-key-change-me")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Enable HTTPS Proxy Header Trust for Render
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.sessions",  # required by admin only
    "django.contrib.messages",  # required by admin only
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",  # makes logout real (B2)
    "adapters.persistence.django_orm",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- CORS & CSRF ------------------------------------------------------------
# Cross-origin deploy (frontend hosted separately): list the EXACT frontend origin(s) in
# CORS_ALLOWED_ORIGINS (comma-separated, full scheme+host). Never use ALLOW_ALL / "*" with
# credentials — the browser rejects a wildcard Access-Control-Allow-Origin on any request that
# carries the cookie, so auth silently breaks. Empty = same-origin (no CORS needed).
_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True  # required so the httpOnly refresh cookie rides cross-site

# The refresh cookie's SameSite. Same-origin -> "Lax". Cross-origin -> set "None" (which forces
# Secure), otherwise the browser won't send it on the boot /api/auth/refresh/ XHR.
REFRESH_COOKIE_SAMESITE = os.getenv("REFRESH_COOKIE_SAMESITE", "Lax")

_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- database --------------------------------------------------------------
# Supabase pooler (port 6543) runs pgBouncer in transaction mode, which breaks server-side
# cursors and long-lived connections. When the URL points at the pooler, set:
#   DB_POOLED=true  -> DISABLE_SERVER_SIDE_CURSORS + CONN_MAX_AGE=0
# Direct connection (5432) needs neither. (LLD §11.3 / B1 note.)
# MODE (DEV | PROD | TEST) is the single switch for which database is used. ONLY PROD talks to
# the real Postgres (DATABASE_URL). DEV and TEST always use local SQLite — even when a
# DATABASE_URL is present in the environment — so local development and tests can never read or
# write the production database by accident. (test.py further specialises to in-memory SQLite.)
MODE = os.getenv("MODE", "DEV").upper()

if MODE == "PROD":
    _database_url = os.getenv("DATABASE_URL")
    if not _database_url:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured("MODE=PROD requires DATABASE_URL to be set.")
    # Supabase pooler (port 6543, pgBouncer transaction mode) breaks server-side cursors and
    # long-lived connections. When the URL points at the pooler, set DB_POOLED=true. A direct
    # connection (5432) needs neither. (LLD §11.3 / B1 note.)
    _pooled = os.getenv("DB_POOLED", "false").lower() == "true"
    DATABASES = {
        "default": dj_database_url.parse(_database_url, conn_max_age=0 if _pooled else 600)
    }
    if _pooled:
        # The transaction pooler (Supavisor) hands each transaction a different backend, which
        # breaks two psycopg3 defaults: server-side cursors (gone on the next backend) and
        # prepared statements (prepare_threshold=5 → "statement does not exist" under load).
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
        DATABASES["default"].setdefault("OPTIONS", {})["prepare_threshold"] = None
else:
    # DEV / TEST → local SQLite, regardless of DATABASE_URL (production-database safety).
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "django_orm.User"  # ⚠️ set BEFORE the first migration - irreversible (DEC-5)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

# Timestamps are stored UTC; leaderboard period boundaries are computed in Asia/Dhaka by the
# domain (core.domain.periods). Do not change TIME_ZONE to shift the leaderboard.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Image storage: Google Drive when credentials are wired, local filesystem otherwise.
USE_GOOGLE_DRIVE = bool(os.getenv("GOOGLE_CREDENTIALS") or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.authentication.JWTCookieAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",  # public endpoints override explicitly
    ],
    "EXCEPTION_HANDLER": "api.exception_handler.domain_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "anon_post_submit": "5/hour",
        "anon_like": "30/hour",
        "auth_like": "200/day",
        "contact_submit": "5/hour",
        "feedback_submit": "5/hour",
        "login": "10/hour",
        "otp_resend": "3/hour",
    },
    # Cursor pagination is handled per-view via api.pagination (use cases return domain Pages,
    # not querysets), so no DEFAULT_PAGINATION_CLASS.
}

SIMPLE_JWT = {
    "BLACKLIST_AFTER_ROTATION": True,
}

# No Celery, so email and Drive I/O happen inside the request. Without a timeout a hung
# upstream ties up a Gunicorn worker until it dies (LLD §11.5). SMTP backends honour
# EMAIL_TIMEOUT; the Mailjet HTTP backend honours ANYMAIL["REQUESTS_TIMEOUT"] (set in prod);
# the Drive adapter sets its own socket timeout.
EMAIL_TIMEOUT = 10  # seconds

# Throttle counters must be shared across Gunicorn workers. LocMemCache is per-process, so a
# "10/hour" limit would become ~10×workers/hour and drift by which worker serves the request.
# DatabaseCache (a Postgres table via `manage.py createcachetable`) is shared and correct -
# slower than Redis, fine at this scale (LLD §8.6, DEC-8). Tests override this in test.py.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "throttle_cache",
    }
}

# The React SPA is served by Django/Whitenoise from this directory (same-origin, DEC-7). A
# catch-all route (config.urls) returns index.html so client-side routing survives a hard
# refresh. CORS is therefore unnecessary in production.
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

# Logger
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
