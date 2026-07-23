# CI/CD Pipeline Plan

**Status:** plan (not yet built) · **Scope:** backend · **Repo host:** GitHub Actions

This plan defines two pipelines:
1. **PR pipeline** — runs on every pull request into `main`. Gatekeeps quality. Never deploys.
2. **Production pipeline** — runs on merge/push to `main`. Re-runs the gates, then deploys.

---

## 1. The idea in one picture

```
 feature branch ──PR──▶  [ PR pipeline ]  ──✅──▶  merge allowed
                          lint + tests                    │
                          (Postgres service)              ▼
                                                    push to main
                                                          │
                                                          ▼
                                                 [ Production pipeline ]
                                                 gates → migrate → deploy
```

**Rule:** code only reaches production through `main`, and nothing reaches `main` without the
PR pipeline passing. Branch protection enforces it (§5).

---

## 2. PR pipeline (`.github/workflows/pr.yml`)

Runs on `pull_request` targeting `main`. This is the existing `backend-ci.yml`, upgraded with a
real Postgres service so tests run on the same engine as production (closing the "tests only ran
on SQLite" gap).

**Stages (fail fast, in order):**

| Stage | Command | Why |
|---|---|---|
| Install | `pip install -r requirements-dev.txt` | deps |
| Import boundary | `lint-imports` | the hexagon rule — a green test suite won't catch a `core/` framework import |
| Lint | `ruff check .` | style/quality |
| Tests | `pytest` (against a Postgres service) | 197 tests incl. the leaderboard contract suite |

**Postgres service:** a throwaway `postgres:17` container in the workflow; `TEST_DATABASE_URL`
points at it, so integration + contract tests run on real Postgres — never the production pooler.

```yaml
name: pr
on:
  pull_request:
    branches: [main]
    paths: ["plastickothay_dev/backend/**"]
jobs:
  gates:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: plastickothay_dev/backend } }
    services:
      postgres:
        image: postgres:17
        env: { POSTGRES_PASSWORD: postgres, POSTGRES_DB: pk_test }
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5
    env:
      TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/pk_test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements-dev.txt
      - run: lint-imports
      - run: ruff check .
      - run: pytest
```

---

## 3. Production pipeline (`.github/workflows/deploy.yml`)

Runs on `push` to `main` (i.e. after a PR merges). Re-runs the gates (never trust that the PR
branch matched what actually landed), then deploys.

**Stages:**

| Stage | What |
|---|---|
| Gates | same as PR — lint-imports, ruff, pytest on a Postgres service |
| Build | (frontend later) `npm run build` → `frontend/dist`; collectstatic |
| Migrate | `manage.py migrate` against the **production** DB |
| Cache table | `manage.py createcachetable throttle_cache` (idempotent) |
| Seed | `manage.py seed_rules` (idempotent) |
| Release | restart the app (gunicorn) — platform-specific (Render deploy hook / SSH / container push) |

Deploy runs **only if the gates job succeeds** (`needs: gates`). Migrations run against prod
using secrets, not committed values.

```yaml
name: deploy
on:
  push:
    branches: [main]
    paths: ["plastickothay_dev/backend/**"]
jobs:
  gates:
    # ...identical to the PR gates job...
  deploy:
    needs: gates            # deploy ONLY if gates pass
    runs-on: ubuntu-latest
    environment: production # GitHub environment for approval + secrets
    defaults: { run: { working-directory: plastickothay_dev/backend } }
    env:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
      DB_POOLED: ${{ secrets.DB_POOLED }}
      DJANGO_KEY: ${{ secrets.DJANGO_KEY }}
      ALLOWED_HOSTS: ${{ secrets.ALLOWED_HOSTS }}
      MAILJET_API_KEY: ${{ secrets.MAILJET_API_KEY }}
      MAILJET_SECRET_KEY: ${{ secrets.MAILJET_SECRET_KEY }}
      DEFAULT_FROM_EMAIL: ${{ secrets.DEFAULT_FROM_EMAIL }}
      GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: python manage.py migrate --noinput
      - run: python manage.py createcachetable throttle_cache
      - run: python manage.py seed_rules
      - run: python manage.py collectstatic --noinput
      # - final release step depends on the host (see §6)
```

> **Migration safety:** run `migrate` against a pooled Supabase URL only if it's the session
> pooler (5432) or direct — the transaction pooler (6543) is fine for the app but not ideal for
> DDL. Point the deploy's `DATABASE_URL` at the session/direct endpoint; the app runtime can
> still use 6543.

---

## 4. Secrets

All real values live in **GitHub → Settings → Secrets → Actions** (and a `production`
environment for deploy-only secrets). Nothing sensitive is committed. The repo carries only
`.env.*.example` files with demo values (see `backend/.env.*.example`).

Required secrets: `DATABASE_URL`, `DB_POOLED`, `DJANGO_KEY`, `ALLOWED_HOSTS`,
`MAILJET_API_KEY`, `MAILJET_SECRET_KEY`, `DEFAULT_FROM_EMAIL`, `GOOGLE_CREDENTIALS`.

---

## 5. Branch protection (GitHub → Settings → Branches → `main`)

- ✅ Require a pull request before merging
- ✅ Require status checks to pass → select the **PR `gates`** job
- ✅ Require branches to be up to date before merging
- ✅ (optional) Require a review approval
- ✅ (optional) Require the `production` environment to need manual approval before deploy

This is what makes "nothing reaches main without passing" real rather than a convention.

---

## 6. The release step (choose per host)

The pipeline above stops before the actual restart because it's host-specific. Options:

- **Render / Railway:** a deploy hook URL — `curl -X POST $RENDER_DEPLOY_HOOK`. Render then pulls
  main, installs, and runs a `build.sh` that does migrate/collectstatic.
- **VPS (SSH):** an `appleboy/ssh-action` step that pulls, installs, migrates, and
  `systemctl restart gunicorn`.
- **Container:** build + push an image, then the platform rolls it out.

Pick one when the host is chosen; the gates/migrate stages above stay the same.

---

## 7. Build order

1. Rename/replace the current `backend-ci.yml` with `pr.yml` (adds the Postgres service). ← easy, do first
2. Add `deploy.yml` gates + migrate stages.
3. Add the host-specific release step (§6) once the deploy target is decided.
4. Turn on branch protection (§5).

Steps 1–2 are pure repo config and can land now. Step 3 waits on the hosting decision.
