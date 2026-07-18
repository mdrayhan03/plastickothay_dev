"""Base settings shared by every environment.

Database selection follows the agreed strategy: if DATABASE_URL is set (Supabase/Postgres in
prod), use it; otherwise fall back to local SQLite. Engine choice is a settings value, not a
hand-rolled factory — Django already gives that for free (LLD §1.1, discussion).
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_KEY", "dev-insecure-key-change-me")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.sessions",  # required by admin only
    "django.contrib.messages",  # required by admin only
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",  # makes logout real (B2)
    "adapters.persistence.django_orm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
_database_url = os.getenv("DATABASE_URL")
_pooled = os.getenv("DB_POOLED", "false").lower() == "true"

if _database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=0 if _pooled else 600,
        )
    }
    if _pooled:
        # Supabase's transaction pooler (Supavisor, port 6543) hands each transaction a
        # different backend connection. That breaks two psycopg3 defaults:
        #   - server-side cursors (a cursor opened on one backend is gone on the next)
        #   - prepared statements (prepare_threshold defaults to 5; a statement prepared on
        #     one backend "does not exist" on another → intermittent errors under load)
        # Disable both. For the session pooler (5432) neither is needed, but both are harmless.
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
        DATABASES["default"].setdefault("OPTIONS", {})["prepare_threshold"] = None
else:
    # Local/dev fallback. Integration + contract tests that need real Postgres behaviour
    # (concurrency, partial indexes under load) must run against DATABASE_URL, not this.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "django_orm.User"  # ⚠️ set BEFORE the first migration — irreversible (DEC-5)

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
