# B0 Implementation Report — Hexagon Skeleton

**Milestone:** B0 · **Branch:** `backend` · **Date:** 2026-07-17
**Status:** ✅ Complete. All exit criteria verified.
**Refs:** `backend_lld.md`, `backend_implementation_plan.md`

---

## 1. Exit criteria — verified, not assumed

| Criterion | Result |
|---|---|
| `pytest` green **with no database** | ✅ **76 passed in 0.07s** |
| `lint-imports` green | ✅ **4 contracts kept, 0 broken** |
| `ruff check` clean | ✅ **All checks passed** |

The first row is the one that matters, so it was verified rather than asserted:

```
$ pip list                 → pytest, ruff, import-linter, and their deps. Nothing else.
$ python -c "import django"     → not installed
$ python -c "import psycopg"    → not installed
$ python -c "import rest_framework" → not installed
$ pg_isready                    → /tmp:5432 - no response
$ pytest                        → 76 passed in 0.07s
```

**Django is not installed. PostgreSQL is not running. 76 tests covering every business rule
pass in 70 milliseconds.** That is the proof the hexagon is real: had the domain leaked into
a framework, none of it could run.

### The boundary is now mechanically enforced

`import-linter` runs four contracts (`pyproject.toml`):

| Contract | Forbids |
|---|---|
| `core is framework-free` | `django`, `rest_framework`, `psycopg`, `bson`, `mongoengine`, `google`, `googleapiclient`, `anymail`, `celery` |
| `core does not depend on adapters or api` | `adapters`, `api`, `config` |
| `domain does not depend on ports or application` | inward-only dependencies |
| `layered core` | `application → ports → domain`, never upward |

This is the highest-value artefact in B0. A green test suite would *not* catch someone
importing `django.utils.timezone` "just here" — and one such import is all it takes for the
DB port to quietly become fiction. **Wire `lint-imports` into CI before B1.**

---

## 2. What was built

53 files under `backend/`. 2,329 lines of `core/`, 1,498 lines of tests.

```
backend/
├── pyproject.toml          pytest + ruff + import-linter contracts
├── core/
│   ├── domain/             ids, errors, value_objects, entities,
│   │                       pagination, read_models, periods, points
│   ├── ports/              clock, unit_of_work, storage, notifications,
│   │                       security, repositories
│   └── application/        accounts/ reports/ engagement/ content/ scoring/
└── tests/
    ├── conftest.py         fixtures + builders (no Django, no settings, no DB)
    ├── fakes/              system.py, repositories.py, seed.py
    ├── unit/               domain/ (41 tests), application/ (35 tests)
    └── contract/           empty — populated at B5
```

### Use cases implemented (all 27)

| Module | Use cases |
|---|---|
| `accounts` | RegisterUser, VerifyOTP, ResendOTP, Login, RefreshToken, Logout, RequestPasswordReset, ResetPassword, GetProfile, UpdateProfile, ListUsers, SetUserRole, SetUserActive |
| `reports` | SubmitReport, ListReports, GetReport, ListMapMarkers, ListOwnReports, UpdateReportDescription, ApproveReport, RejectReport, HideReport, UnhideReport, ListReportsForReview, GetPostStats |
| `engagement` | LikePost, UnlikePost, SubmitFeedback, SubmitContactMessage, ListFeedback, ListContactMessages |
| `content` | GetContactPage, UpdateContactPage |
| `scoring` | GetLeaderboard, GetContribution |

---

## 3. Test coverage

| File | Tests | Covers |
|---|---|---|
| `test_points.py` | 34 | every rule in LLD §5.3 |
| `test_periods.py` | 7 | Dhaka-time period boundaries |
| `test_submit_report.py` | 11 | anonymous/authenticated split, failure compensation |
| `test_likes.py` | 12 | one-like-per-post, self-like, anonymous |
| `test_moderation.py` | 12 | approve/reject/hide/unhide, audit, DEC-2 round-trip |
| **Total** | **76** | |

### Rules proven green, with no database

- ✅ Anonymous like awards **nobody** — including the post owner (DEC-1)
- ✅ Self-like awards zero to **both** sides
- ✅ Likes on pending/hidden posts award nothing
- ✅ **Hiding an approved post strips its points *and* its likes' points**
- ✅ **Un-hiding restores both** — no re-award path exists
- ✅ Inactive rules pay zero but still count the engagement
- ✅ Rule changes are retroactive (DEC-2, accepted; mitigated by POL-1)
- ✅ Posts bucket by approval date, not creation date (DEC-3)
- ✅ Week boundaries land at Dhaka midnight, not UTC
- ✅ Authenticated submit ignores client-supplied name/email/phone
- ✅ A failed insert deletes the orphaned Drive upload
- ✅ `unhide` preserves the original `approved_at`

The clearest proof of DEC-2 is `test_hide_then_unhide_round_trips_the_score`: a score goes
**103 → 0 → 103** across hide/unhide, and **no moderation use case contains a single line of
point logic.** The status moves; the score follows. That is the entire argument for the
derived model over a ledger, executable.

---

## 4. Deviations from the LLD

Three places where implementation improved on the design doc.

### 4.1 Orphaned upload compensation (new)

The LLD's `SubmitReport` sketch put the Drive upload inside the `uow` block. **Drive is not
transactional.** If the DB insert fails after a successful upload, the file orphans in Drive
forever. Now: upload → try insert → on any failure, delete the uploaded file and re-raise.
Covered by `test_insert_failure_deletes_the_orphaned_upload`.

### 4.2 Post-commit side effects (clarified)

The LLD showed image deletion and email inside the moderation flow. Both now run **after**
commit: a Mailjet outage or a Drive failure must not roll back a moderation decision that
already committed. With no Celery, they are best-effort and deliberately swallowed. Covered
by `test_mail_failure_does_not_undo_approval`.

### 4.3 `OTP` entity (missing from LLD §4.2)

The LLD declared `OTPRepository` but never defined the `OTP` entity. Added, with
`purpose` (registration vs password reset) so a registration code cannot be replayed against
password reset.

---

## 5. Findings

### 5.1 A test was wrong — and the code was right

`test_inactive_rule_contributes_zero` asserted that a like under an inactive rule is "still
counted" for the receiver but that the **giver vanishes entirely**. Those two claims
contradict each other. The implementation was consistent: both sides are counted, both worth
zero. Bob's contribution page should still say "1 like given" even when the rule pays
nothing.

The test was fixed, and the distinction documented: an **inactive rule** still counts the
engagement at zero points, whereas an **anonymous** like is not counted for either side
because it can never earn.

### 5.2 `def list()` shadows the builtin

`PostRepository.list()` made the later annotation `-> list[MapMarker]` resolve to the method,
not the builtin — `TypeError: 'function' object is not subscriptable` at import. Fixed with
`from __future__ import annotations` in both affected modules. Worth knowing before writing
the Django repositories at B1, which have the same shape.

### 5.3 Legacy code is local-only

`backend_old/` is gitignored (`.gitignore:56`). It is reference material for porting
behaviour (OTP flow, filter semantics, Drive/Mailjet calls) and never enters this branch.
The real history lives on `main`. Nothing to do — just be aware the reference disappears on
a fresh clone.

---

## 6. Open — needs a decision

| # | Item | Detail |
|---|---|---|
| **1** | **Level thresholds are a placeholder** | `tests/fakes/seed.py` uses 0/100/300/700/1500 (Newcomer → Champion). **These are my guess, not your decision.** The legacy "every 5 points = 1 level" is meaningless now one approved post is worth 100. Table-driven, so changing them is data — but they need a product call before launch. |
| **2** | **Week starts Monday** | `periods.py` uses ISO-8601 (Monday). Bangladesh commonly treats the week as starting Sunday. One constant (`WEEK_STARTS_ON_MONDAY`), but it silently changes every weekly leaderboard. Confirm. |
| **3** | **Docker for integration tests?** | Still unanswered. The leaderboard SQL is Postgres-only by choice, so its contract test can only run against real Postgres. Docker → throwaway container. No docker → Supabase test schema, slower CI. Needed by B5, decided at B1. |

---

## 7. What is NOT built

B0 is the hexagon only. Deliberately absent:

- No Django project, settings, or `manage.py` — B1
- No ORM models, migrations, or mappers — B1
- No DRF views, serializers, or URLs — B2+
- No real adapters (Drive, Mailjet, SimpleJWT, Postgres) — B1–B3
- `tests/contract/` is an empty package — B5, when there are two implementations to compare
- No CI pipeline — **wire `lint-imports` in before B1**

---

## 8. Next: B1

**Hard blocker: the Supabase `DATABASE_URL`.**

| Needed | Note |
|---|---|
| `DATABASE_URL` | ⛔ blocks B1 entirely |
| Pooler (6543) or direct (5432)? | Pooler runs pgBouncer in transaction mode → needs `DISABLE_SERVER_SIDE_CURSORS = True` and `CONN_MAX_AGE = 0`. Better decided now than debugged at B5. |
| `DJANGO_KEY` | I can generate a dev one |
| Mailjet keys | soft — console backend stubs it (B2) |
| Drive service account | soft — fake adapter stubs it (B3) |

**The irreversible bit:** `AUTH_USER_MODEL` must be set before the first migration runs.
Changing it afterwards is one of the genuinely painful operations in Django, so B1 should be
reviewed before B2 begins.
