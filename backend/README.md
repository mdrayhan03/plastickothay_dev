# PlasticKothay Backend

Django REST API for PlasticKothay, built with a **hexagonal (ports & adapters)** architecture:
a framework-free domain core with Django/DRF as one set of adapters around it.

- **Architecture & decisions:** `../documents/backend_lld.md`
- **Milestone history & reports:** `../documents/backend_milestones_b1_b7.md`, `b0`/`b1`/`b2_b7` reports

## Layout

```
core/         THE HEXAGON - pure Python, no framework imports (enforced by import-linter)
  domain/       entities, value objects, errors, point rules, periods
  ports/        abstract interfaces (repositories, storage, notifications, security, ...)
  application/  use cases
adapters/     driven side - Django ORM, Google Drive / local storage, Mailjet, SimpleJWT
api/          driving side - DRF views, serializers, auth, permissions, throttling
config/       settings (base/dev/prod/test), urls, container (composition root)
tests/        unit (no DB) · integration (DB) · contract (leaderboard: fake vs ORM)
```

**The rule:** nothing under `core/` may import `django`, `rest_framework`, `psycopg`,
`google`, etc. CI runs `import-linter` to enforce it - a green test suite won't catch a leak.

## Setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # runtime + test tooling
cp .env.example .env                            # fill in as needed (works empty for dev)
```

With an empty `.env` the backend uses SQLite, console email, and local file storage - no
external services required.

## Run

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_rules            # point & level rules
.venv/bin/python manage.py runserver
```

- API: `http://localhost:8000/api/`  ·  Health: `/api/health/`  ·  Django admin: `/django-admin/`
- Django admin manages **config tables only** (point rules, levels, contact page). Everything
  with behaviour goes through the API.

## Test & quality gates

```bash
.venv/bin/pytest            # 188 tests (unit + integration + contract)
.venv/bin/lint-imports      # hexagon boundary - must stay 4/4
.venv/bin/ruff check .      # lint
```

Unit tests run with **no database**. Integration/contract tests default to in-memory SQLite;
set `TEST_DATABASE_URL` to a local Postgres for full-fidelity runs (never the prod pooler).

## Deploy (prod)

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
# required env: DATABASE_URL, DB_POOLED, DJANGO_KEY, ALLOWED_HOSTS,
#   MAILJET_API_KEY, MAILJET_SECRET_KEY, DEFAULT_FROM_EMAIL,
#   GOOGLE_CREDENTIALS (or GOOGLE_SERVICE_ACCOUNT_FILE)
pip install -r requirements.txt
python manage.py migrate
python manage.py createcachetable throttle_cache   # required - throttles use DatabaseCache
python manage.py seed_rules
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

The React SPA is served same-origin by Whitenoise from `../frontend/dist`, so the httpOnly
refresh cookie stays first-party and CORS is unnecessary.
