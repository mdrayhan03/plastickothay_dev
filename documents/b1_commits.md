# B1 Commit List - copy-paste ready

**Branch:** `backend` · **Milestone:** B1 (persistence & identity)
**Status:** code complete, 91 tests green (76 unit + 15 integration), validated against SQLite.
Real-Postgres validation pending `DATABASE_URL`.

> **The exit-128 fix.** Each cell is wrapped in `( … )` - a subshell. `set -e` inside a
> subshell exits only the subshell on failure, never your terminal. The previous B0 block ran
> `set -e` in your login shell, so one failing command killed the terminal (exit 128). This
> pattern cannot do that.

Run each cell from **anywhere inside the repo**. Four cells, in order.

---

## Cell 1 - Django scaffold, settings, deps

```bash
(
  set -e
  cd "$(git rev-parse --show-toplevel)"
  CO="Co-Authored-By: mdrayhan03"

  git add backend/requirements.txt backend/requirements-dev.txt backend/manage.py \
          backend/config/__init__.py backend/config/urls.py backend/config/wsgi.py \
          backend/config/settings/__init__.py backend/config/settings/base.py \
          backend/config/settings/dev.py backend/config/settings/prod.py \
          backend/config/settings/test.py backend/pyproject.toml backend/.gitignore
  git commit -m "chore(backend): add Django project scaffold and settings" -m "Django 5.2 + DRF + SimpleJWT + psycopg enter the project. Settings are split base/dev/prod/test.

Database selection is a settings value, not a hand-rolled factory: DATABASE_URL (Supabase/Postgres) if set, else local SQLite. The Supabase pooler (6543) needs DISABLE_SERVER_SIDE_CURSORS + CONN_MAX_AGE=0, toggled via DB_POOLED - the direct connection (5432) needs neither.

AUTH_USER_MODEL is set here, before any migration - irreversible afterwards (DEC-5). TIME_ZONE stays UTC; leaderboard periods are bucketed in Asia/Dhaka by the domain, not by settings.

Refs: backend_lld.md 9.1, 11.2, 11.3; DEC-5, DEC-7" -m "\$CO"

  echo "✅ cell 1 done"; git log --oneline -1
)
```

## Cell 2 - ORM models, migration, mappers

```bash
(
  set -e
  cd "$(git rev-parse --show-toplevel)"
  CO="Co-Authored-By: mdrayhan03"

  git add backend/adapters/__init__.py backend/adapters/persistence/__init__.py \
          backend/adapters/persistence/django_orm/__init__.py \
          backend/adapters/persistence/django_orm/apps.py \
          backend/adapters/persistence/django_orm/models.py \
          backend/adapters/persistence/django_orm/migrations/__init__.py \
          backend/adapters/persistence/django_orm/migrations/0001_initial.py \
          backend/adapters/persistence/django_orm/mappers.py \
          backend/api/__init__.py
  git commit -m "feat(persistence): add ORM models, initial migration and mappers" -m "All 12 tables (LLD §9.2) as Active-Record models - a persistence detail, never the domain. Mappers translate ORM rows to core.domain dataclasses; nothing above the repository sees a model.

Custom User (AbstractUser). Role is derived from is_superuser/is_staff in the mapper, not stored - there is no role column. is_verified (completed OTP) is kept distinct from is_active (not banned).

The like-uniqueness rule is a PARTIAL unique index - WHERE type='like' AND actor_user IS NOT NULL - so comments stay unconstrained and anonymous likes are not bound (nothing identifies them, which is why they earn no points, DEC-1). Post/Feedback carry range check constraints; ContactPage is a pinned singleton.

Refs: backend_lld.md 2.2, 9.1, 9.2, 9.3; DEC-1, DEC-5" -m "\$CO"

  echo "✅ cell 2 done"; git log --oneline -1
)
```

## Cell 3 - repositories, adapters, unit-of-work, container

```bash
(
  set -e
  cd "$(git rev-parse --show-toplevel)"
  CO="Co-Authored-By: mdrayhan03"

  git add backend/adapters/persistence/django_orm/repositories.py \
          backend/adapters/persistence/django_orm/unit_of_work.py \
          backend/adapters/security/__init__.py \
          backend/adapters/security/password_hasher.py \
          backend/adapters/system/__init__.py backend/adapters/system/clock.py \
          backend/config/container.py
  git commit -m "feat(persistence): add ORM repositories, unit-of-work and composition root" -m "Every repository port except LeaderboardRepository (that's B5). Each returns domain entities - never a model, never a QuerySet. Cursor pagination is keyset over (created DESC, id DESC), stable under inserts.

Unique-violation translation happens at the DB, not via a pre-check: UserRepository.add wraps the insert in a SAVEPOINT so a caught IntegrityError does not poison the request's outer transaction, then re-raises UsernameTaken/EmailTaken. EngagementRepository.add does the same and re-raises AlreadyLiked. Without the savepoint the next query in the request fails with TransactionManagementError - caught during integration testing.

DjangoUnitOfWork wraps transaction.atomic() so use cases declare boundaries without importing Django. Container wires ports to adapters as plain factories - no DI framework.

Refs: backend_lld.md 6, 7.2, 8.4; DEC-1" -m "\$CO"

  echo "✅ cell 3 done"; git log --oneline -1
)
```

## Cell 4 - seed command, integration tests, docs

```bash
(
  set -e
  cd "$(git rev-parse --show-toplevel)"
  CO="Co-Authored-By: mdrayhan03"

  git add backend/adapters/persistence/django_orm/management/__init__.py \
          backend/adapters/persistence/django_orm/management/commands/__init__.py \
          backend/adapters/persistence/django_orm/management/commands/seed_rules.py \
          backend/tests/integration/__init__.py \
          backend/tests/integration/test_repositories.py
  git commit -m "test(persistence): add rule seed command and repository integration tests" -m "seed_rules is idempotent and mirrors tests/fakes/seed.py so fake and real DB start identical. Level thresholds remain a PLACEHOLDER pending a product decision.

15 integration tests against a real database (SQLite locally, Postgres in CI): mapper round-trips, role<->flag mapping, unique-violation translation, cursor pagination walks every row without gaps, and the partial unique index blocks a duplicate like while anonymous likes stack. Concurrency (two likes racing the index) needs real Postgres and is deferred to B5 - SQLite serialises writers.

The unit suite still runs DB-free; import-linter still keeps core/ framework-free (4/4).

Refs: backend_lld.md 5.2, 9.3, 12" -m "\$CO"

  git add documents/backend_milestones_b1_b7.md documents/b1_commits.md documents/b1_implementation_report.md
  git commit -m "docs: add B1 report, milestone breakdown and commit list" -m "Refs: backend_milestones_b1_b7.md" -m "\$CO"

  echo "✅ all B1 cells done"; git log --oneline -6; git status --short
)
```

---

## After committing - verify

```bash
cd "$(git rev-parse --show-toplevel)/backend"
.venv/bin/pytest            # 91 passed
.venv/bin/lint-imports      # 4 kept, 0 broken
.venv/bin/ruff check .      # All checks passed
git status                  # clean (db.sqlite3, .venv, staticfiles ignored)
```
