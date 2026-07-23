# B2–B7 Implementation Report — Full API & Cutover

**Milestones:** B2–B7 · **Branch:** `backend` · **Date:** 2026-07-18
**Status:** ✅ All complete. **188 tests green** (76 unit, 92 integration, 20 contract), 4/4
import contracts, ruff clean.
**Refs:** `backend_lld.md`, `backend_milestones_b1_b7.md`, `b0/b1` reports.

---

## 1. Headline

The backend is feature-complete. Every endpoint in the LLD contract (§10) exists, is tested,
and enforces its access level. The hexagon held the whole way: Django, DRF, SimpleJWT, and
Google libraries were all bolted on, and `core/` still imports none of them — proven on every
commit by `import-linter` (4 contracts kept).

| Layer | Count |
|---|---|
| Endpoints | 31 across auth, me, reports, engagement, scoring, content, admin |
| Tests | 188 (76 unit · 92 integration · 20 contract) |
| Commits (B1–B7) | 23 |

---

## 2. What each milestone delivered

### B2 · Auth vertical slice
`SimpleJWTTokenService` behind the `TokenService` port; refresh tokens revocable via the
blacklist app (real logout). `JWTCookieAuthentication` returns `None` (not 401) with no token,
so anonymous callers reach `AllowAny`. One exception handler maps `DomainError` → HTTP with a
single envelope. Refresh token in an httpOnly/Secure/SameSite=Lax cookie scoped to `/api/auth/`;
access token in the body for the SPA to hold in memory. **14 tests** including the security
cases: wrong password is 400 not 403 (can't confirm the account), revoked token can't rotate.

### B3 · Reports
Local + Google Drive `ImageStorage` adapters (Drive builds its client lazily, so importing
needs no creds). **The public/admin serializer split closes the legacy PII leak** —
`PublicPostSerializer` exposes reporter *name only*; email/phone live exclusively on
`AdminPostSerializer` behind an admin token. Base64 decoded at the serializer. **11 tests**,
including three PII regression tests (one scans the raw response body for the address itself).

### B4 · Moderation
approve / reject / hide / unhide / review-list / stats, all `IsStaffOrAdmin`. **No point code
anywhere** — points derive from `Post.status` (DEC-2). Reject soft-deletes + removes the Drive
image; side effects run after commit so a mail/Drive failure can't undo a decision. **12 tests**
across the permission ladder and lifecycle.

### B5 · Engagement & scoring
Like/unlike (anonymous allowed, awards nobody — DEC-1). `DjangoLeaderboardRepository`
implements the calculation strategy in the ORM (portable, runs on SQLite and Postgres). **The
contract suite is the centrepiece**: 10 scenarios run against *both* the reference
implementation (`core.domain.points`) and the ORM aggregation — 20 tests — asserting identical
numbers. This is the guard against SQL/Python drift; any future leaderboard implementation is
"done" only when it passes the same suite. Plus **10 API tests**.

### B6 · Content
Contact page (public read / admin write, structured fields not a blob), contact messages,
feedback (never public). Django admin registers **config tables only** (PointRule, LevelRule,
ContactPage); two guard tests assert `Post`/`Engagement` are *not* registered — approving has
behaviour that must go through use cases. **12 tests**.

### B7 · Hardening & cutover
`DatabaseCache` for throttles (shared across workers; LocMemCache would multiply limits by
worker count — DEC-8). Same-origin SPA serving via a catch-all route, so the httpOnly cookie
stays first-party and CORS is unnecessary. **The permission matrix test** pins every endpoint's
access level across {anonymous, user, staff}. CI workflow runs all three gates. **19 tests**.

---

## 3. Findings during the build

- **DRF throttle poisoned the request transaction (B1→B3).** A caught `IntegrityError` inside
  an atomic block marks the whole transaction broken; `LikePost` reads `count()` right after
  catching `AlreadyLiked`, which would 500 in production. Fixed with savepoints around
  constraint inserts. (Surfaced in B1 integration tests, load-bearing for B5 likes.)
- **`DomainUser` needed `pk`.** DRF throttling reads `request.user.pk` for its cache key; the
  lightweight token-claims user had only `id`. Added.
- **A moderation test was wrong, not the code.** It submitted a report *as the admin* then
  asserted the anonymous email — but the spoofing guard correctly used the admin's profile.
  Test fixed; the guard is what we wanted.
- **Throttle state leaked across tests.** The 5/hour submit limit accumulated in the shared
  cache. Fixed with an autouse cache-clear fixture; dedicated throttle tests drive the limit
  explicitly.

---

## 4. Deviation from the LLD: leaderboard is ORM, not raw SQL

The LLD §5.4 specified raw Postgres SQL. Implemented in the Django ORM instead, because:
- it runs on SQLite in tests (no docker dependency, contract suite runs everywhere), and on
  Postgres in prod, unchanged;
- it stays behind `LeaderboardRepository`, so a raw-SQL or materialized-view version can drop
  in later — and must pass the same contract suite.

This is the pragmatic call argued during design ("I lean toward the ORM version"). The escape
hatch (materialized view behind the port) is documented in `leaderboard.py`.

---

## 5. What is NOT done / open

| # | Item | Note |
|---|---|---|
| 1 | **Real-Postgres run of the new API tests** | B1 was validated on Supabase; B2–B7 tests ran on SQLite. Recommend one CI/local run against a Postgres before production (esp. the leaderboard aggregation and the partial-index concurrency). |
| 2 | **Concurrency test for double-like** | Still deferred — needs real Postgres (SQLite serialises writers). |
| 3 | **Mailjet & Drive live** | Both stubbed (console email, local storage). Set `MAILJET_*` and `GOOGLE_CREDENTIALS` to activate; the ports mean no code changes. |
| 4 | **SPA static assets** | `SPAView` serves `frontend/dist/index.html` (placeholder until built). The Vite build's `/assets/*` wiring into Whitenoise is a frontend+deploy task. |
| 5 | **`createcachetable`** | Prod needs `manage.py createcachetable throttle_cache` before throttling works (dev/test use LocMemCache). |
| 6 | **Level thresholds & week-start** | Still the placeholder values (0/100/300/700/1500; Monday). Product decisions. |
| 7 | **Timeouts on Drive/Mailjet** | The synchronous-I/O timeouts (Drive 30s, Mailjet 10s) are noted but not yet enforced in the adapters. |

**None block the frontend from integrating** — the API is live and contract-complete.

---

## 6. Deployment checklist (for reference)

```bash
# prod env: DATABASE_URL, DB_POOLED, DJANGO_KEY, MAILJET_*, DEFAULT_FROM_EMAIL,
#           GOOGLE_CREDENTIALS (b64) or GOOGLE_SERVICE_ACCOUNT_FILE, ALLOWED_HOSTS
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py createcachetable throttle_cache
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py seed_rules
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

---

## 7. Next

The backend milestones are complete. Natural next steps: (a) one real-Postgres CI run to close
item 1, (b) wire live Mailjet/Drive credentials, (c) begin the **frontend** (F0–F5) against this
now-stable API contract, and (d) delete `backend_old/` once nothing else references it.
