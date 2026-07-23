"""Test settings.

Unit tests (tests/unit) need none of this — they run on fakes with no Django. This module is
for the DRF/API and integration tests added from B2 onward.

Tests must NEVER touch the remote Supabase database: running against the transaction pooler is
slow and leaves dangling `test_*` databases the pooler won't let you drop. So DATABASE_URL from
.env is deliberately ignored here. Default is in-memory SQLite (fast, isolated). For
full-fidelity Postgres runs (constraints, concurrency), point TEST_DATABASE_URL at a LOCAL
Postgres — a docker container in CI, never the production pooler.
"""

import os

from config.settings.base import *  # noqa: F401,F403

_test_db = os.getenv("TEST_DATABASE_URL")
if _test_db:
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(_test_db)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# In-process cache — no createcachetable needed, and throttle counters still work within a
# test (a single process). Prod uses DatabaseCache (shared across workers).
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Faster password hashing in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
