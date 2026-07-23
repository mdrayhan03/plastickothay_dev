# B1 Implementation Report — Persistence & Identity

**Milestone:** B1 · **Branch:** `backend` · **Date:** 2026-07-18
**Status:** ✅ Code complete. Validated against SQLite. Real-Postgres validation pends `DATABASE_URL`.
**Refs:** `backend_lld.md`, `backend_milestones_b1_b7.md`

---

## 1. What was built

Django entered the project. The domain gained a database without the domain learning about it.

| Area | Files |
|---|---|
| Scaffold | `manage.py`, `config/{urls,wsgi}.py`, `config/settings/{base,dev,prod,test}.py` |
| Models | `adapters/persistence/django_orm/models.py` — 12 tables + `0001_initial` migration |
| Mapping | `mappers.py` — ORM row ↔ domain dataclass, both directions |
| Repositories | `repositories.py` — every port except `LeaderboardRepository` (B5) |
| Transaction | `unit_of_work.py` — `transaction.atomic()` behind the port |
| System adapters | `clock.py`, `security/password_hasher.py` |
| Wiring | `config/container.py` — composition root |
| Seed | `manage.py seed_rules` — point + level rules, idempotent |
| Tests | `tests/integration/test_repositories.py` — 15 tests, real DB |
| Deps | `requirements.txt` (runtime), `requirements-dev.txt` (tooling) |

---

## 2. Exit criteria

| Criterion | Result |
|---|---|
| Migrations apply cleanly | ✅ against SQLite; ⏳ Supabase pending `DATABASE_URL` |
| Repository integration tests green | ✅ **15 passed** |
| Unit suite still DB-free | ✅ **76 passed**, no DB touched |
| `import-linter` still 4/4 | ✅ Django did **not** leak into `core/` |
| Partial unique index rejects duplicate like at DB level | ✅ verified |
| `ruff` clean | ✅ |
| **Total** | **91 passed in 0.33s** |

The load-bearing check is row 3+4: Django is now a project dependency, yet the unit suite runs
without a database and `core/` imports nothing framework-shaped. The hexagon held while its
first real adapter was bolted on.

---

## 3. Findings

### 3.1 A real transaction bug, caught by an integration test

The most valuable thing B1 produced. When the DB raises `IntegrityError` **inside** an atomic
block, Django marks the whole transaction broken — every subsequent query then raises
`TransactionManagementError` until the block exits.

`LikePost` catches `AlreadyLiked` and then reads `count()` to return the new like total — in
the same request, the same transaction. Without protection that `count()` would crash in
production, turning a duplicate-like (a 409) into a 500.

**Fix:** wrap each constraint-bearing insert (`User.add`, `Engagement.add`) in its own
`transaction.atomic()` savepoint. The `IntegrityError` now rolls back only the savepoint; the
surrounding transaction survives, and the re-raised domain error is handled cleanly. Proven by
`test_partial_unique_index_blocks_duplicate_like`, which asserts `count() == 1` *after* the
rejected duplicate.

This is exactly the class of bug the fakes could not surface — it only exists where a real
transaction manager meets a real constraint. It is the reason integration tests exist.

### 3.2 Role is derived, not stored

`user_type` 1/2/3 is gone. `Role` maps to Django's `is_superuser`/`is_staff` flags in the
mapper (`role_from_flags` / `flags_from_role`); there is no role column. This keeps Django's
permission system authoritative and means the admin "make staff/admin" action is just flipping
those flags.

### 3.3 `def list()` shadowing — pre-empted

Flagged in the B0 report as a B1 risk. `from __future__ import annotations` at the top of
`repositories.py` defused it before it bit.

---

## 4. Deviations & decisions made during B1

| # | Decision | Why |
|---|---|---|
| B1-a | **SQLite fallback when `DATABASE_URL` is unset** | Lets the project run and the migration/repo tests pass locally now, and matches the stated "SQLite for test, Postgres for prod" strategy. Integration tests needing real-Postgres behaviour (concurrency) are marked and deferred to B5. |
| B1-b | **Denormalised `post_owner_user` on `Engagement`** | The B5 leaderboard SQL filters likes by the post's owner; storing it on the row (immutable) avoids a self-join at query time. Captured on insert, tested. |
| B1-c | **`requirements.txt` split** | Runtime deps vs dev tooling (`pytest`, `ruff`, `import-linter`) — prod images should not carry the test stack. |
| B1-d | Savepoints around constraint inserts | §3.1. |

---

## 5. What is NOT done in B1

- **Real Postgres validation.** Everything ran against SQLite. Migrations, constraints, and
  the mapper round-trips must be re-verified against Supabase before B2 ships. Only the URL is
  missing.
- **Concurrency test.** Two simultaneous likes racing the partial unique index — SQLite
  serialises writers and cannot reproduce it. Deferred to B5 with real Postgres.
- **No API layer.** No DRF views, serializers, auth, or URLs — that is B2. `config/urls.py`
  mounts only Django admin so far.
- **`db.sqlite3` is git-ignored.** A local dev artefact; never committed.

---

## 6. Blocking / open

| # | Item | Needed by |
|---|---|---|
| 1 | **Supabase `DATABASE_URL`** — re-run migrate + integration tests against real Postgres | before B2 ships |
| 2 | Pooler (6543) or direct (5432)? Sets `DB_POOLED` | with #1 |
| 3 | Docker for CI Postgres, or a Supabase test schema | B5 |
| 4 | Level thresholds (still placeholder 0/100/300/700/1500) | B5 |
| 5 | Week starts Monday (ISO) or Sunday? | B5 |

**None of these block starting B2** — B2 builds the auth API on the repositories, which work
against SQLite for development. #1 is a validation step, best done before B2 is considered
shippable, but it doesn't gate writing B2.

---

## 7. Next: B2 — auth vertical slice

register → OTP → verify → login → refresh → logout, end to end. SimpleJWT behind the
`TokenService` port, httpOnly refresh cookie, the DRF exception handler that maps `DomainError`
→ HTTP, and the cookie-aware auth class that returns `None` (not 401) for anonymous callers.
Mailjet is soft — Django's console backend stubs it, so no keys are needed to build B2.
