# B0 Commit List — copy-paste ready

**Branch:** `backend`
**Total:** 23 commits, 56 files (53 under `backend/`, 3 docs).

> **In a hurry?** §0 below is all 23 commits in ONE block — paste once, get 23 commits.
> §1–23 are the same commits individually if you'd rather go step by step.

---

## 0. Run all 23 commits in one paste

From the **repo root** (`plastickothay_dev/`). `set -e` aborts on the first failure, so a
mistake stops the run rather than half-committing. Nothing is pushed.

```bash
set -e
cd "$(git rev-parse --show-toplevel)"
CO="Co-Authored-By: mdrayhan03"

# 1 ── scaffold & tooling
git add backend/pyproject.toml backend/core/__init__.py backend/core/domain/__init__.py \
        backend/core/ports/__init__.py backend/core/application/__init__.py \
        backend/core/application/accounts/__init__.py backend/core/application/reports/__init__.py \
        backend/core/application/engagement/__init__.py backend/core/application/content/__init__.py \
        backend/core/application/scoring/__init__.py backend/tests/__init__.py \
        backend/tests/fakes/__init__.py backend/tests/unit/__init__.py \
        backend/tests/unit/domain/__init__.py backend/tests/unit/application/__init__.py \
        backend/tests/contract/__init__.py
git commit -m "chore(backend): scaffold hexagonal skeleton and dev tooling" -m "Creates the core/ (domain, ports, application) and tests/ tree for the DRF rewrite, alongside the legacy code which stays untouched until B7.

Adds pytest, ruff and import-linter config. The import-linter contracts are the load-bearing part: they forbid core/ from importing django, rest_framework, psycopg, google, mongoengine, or anything in adapters/api/config. Without mechanical enforcement the boundary erodes silently and the DB port becomes decorative.

Refs: backend_lld.md 2.1, 3" -m "$CO"

# 2 ── domain: identity, errors, value objects
git add backend/core/domain/ids.py backend/core/domain/errors.py backend/core/domain/value_objects.py
git commit -m "feat(domain): add identity types, error tree and value objects" -m "Replaces the magic numbers scattered through the legacy code: status=1 becomes PostStatus.APPROVED, user_type=3 becomes Role.USER. Adds HIDDEN as a status distinct from REJECTED (hide keeps the image, reject deletes it).

Every DomainError carries a stable code that the API exception handler maps to one HTTP status in exactly one place. GeoPoint validates its own range.

Refs: backend_lld.md 4.1, 4.3, 8.5" -m "$CO"

# 3 ── domain: entities
git add backend/core/domain/entities.py
git commit -m "feat(domain): add entities as framework-free dataclasses" -m "Plain dataclasses with no .save() and no ORM. The persistence adapter will map between these and Django models. If this module ever imports Django, the DB port is fiction.

Post carries reporter (always present) and reporter_id (None => anonymous), which is the entire anonymous/authenticated split. User.as_reporter() exists so authenticated submissions take contact details from the stored profile rather than the request body.

Post.approve() sets approved_at once only: re-approving after a hide must not shift the leaderboard bucket.

Refs: backend_lld.md 2.2, 4.2" -m "$CO"

# 4 ── domain: pagination & read models
git add backend/core/domain/pagination.py backend/core/domain/read_models.py
git commit -m "feat(domain): add pagination primitives and read models" -m "PostFilter replaces the legacy overloaded filter param (filter=today|severity_3|accepted), which conflated three orthogonal concerns and could not express 'accepted AND severity 3'.

statuses is not a public query parameter: public use cases pin it to APPROVED, only admin use cases pass anything else.

MapMarker is deliberately not a Post. The map wants thousands of thin markers, the feed wants twenty full records; serving both from one query was the legacy mistake.

Refs: backend_lld.md 8.4" -m "$CO"

# 5 ── domain: leaderboard periods
git add backend/core/domain/periods.py
git commit -m "feat(domain): compute leaderboard period boundaries in Dhaka time" -m "Timestamps are stored UTC, but week/month/year boundaries are computed in Asia/Dhaka. Bucketing in UTC would reset the weekly leaderboard at 06:00 Monday local — mid-morning for every user.

The legacy code mixed datetime.utcnow() and datetime.now(); that is not carried forward. Input and output here are both tz-aware UTC.

Refs: backend_lld.md 5.4" -m "$CO"

# 6 ── domain: point rules
git add backend/core/domain/points.py
git commit -m "feat(domain): add derived point rules" -m "Points are derived from current state — no ledger, no score table (DEC-2). A score is a function of current post statuses x current engagements x active rules, so hiding a post strips its points AND its likes' points automatically, and un-hiding restores them, with no reversal code anywhere.

Four conditions gate an engagement: actor is authenticated, post is publicly approved, post is attributable, actor is not the owner. Condition 1 is a security control, not a product choice (DEC-1) — an anonymous liker has no stable identity, so no unique constraint can bind them, and paying the owner would let a shell loop print points forever.

This module is the SPECIFICATION. Production uses raw SQL, so these rules live in two places and can drift; the contract suite in tests/contract/ is what will stop that.

Refs: backend_lld.md 5.1, 5.2, 5.3; DEC-1, DEC-2" -m "$CO"

# 7 ── ports: infrastructure
git add backend/core/ports/clock.py backend/core/ports/unit_of_work.py backend/core/ports/storage.py \
        backend/core/ports/notifications.py backend/core/ports/security.py
git commit -m "feat(ports): add clock, unit-of-work, storage, notification and security ports" -m "UnitOfWork exists because transaction.atomic() is a Django import and cannot appear in core/, but use cases still need to declare all-or-nothing boundaries. Retrofitting transaction boundaries later is miserable.

Clock makes OTP expiry and period boundaries testable without sleep().

ImageStorage takes decoded bytes, never a base64 string: base64 is transport encoding and is decoded at the serializer.

Notifier speaks domain intent (send_otp), not transport. Django's EMAIL_BACKEND is the transport strategy and lives inside the Mailjet adapter — two layers, deliberately.

Refs: backend_lld.md 6" -m "$CO"

# 8 ── ports: repositories
git add backend/core/ports/repositories.py
git commit -m "feat(ports): add repository ports" -m "Every method accepts and returns domain types — never an ORM model, never a QuerySet. A lazy queryset crossing this boundary would leak persistence semantics into the domain.

LeaderboardRepository is the calculation strategy port: raw Postgres SQL by default, swappable for an ORM or NoSQL implementation without touching any use case.

EngagementRepository.add() must translate the DB's unique-constraint violation into AlreadyLiked rather than checking first — a check-then-act read would let concurrent double-likes through.

Refs: backend_lld.md 6, 7.2" -m "$CO"

# 9 ── reports: submission
git add backend/core/application/reports/dto.py backend/core/application/reports/submission.py
git commit -m "feat(reports): add report submission for anonymous and authenticated users" -m "The request payload is identical either way; the only difference is whether a token is present. Anonymous submissions trust the body; authenticated submissions take name/email/phone from the stored profile and IGNORE the body, otherwise a logged-in user could attach a stranger's contact details to a report.

The Drive upload is not part of the transaction, so a failed insert would orphan the file forever. Added a compensating delete on failure — this was not in the LLD sketch.

Refs: backend_lld.md 7.1" -m "$CO"

# 10 ── reports: public queries
git add backend/core/application/reports/queries.py
git commit -m "feat(reports): add public listing, detail, map and description update" -m "Public listing pins statuses to APPROVED in the USE CASE, not the view and never from a query param.

This closes a live leak in the legacy code: posts() defaulted to Post.objects() — every post regardless of status — which combined with the planned serializer exposing email and pN would have published the name, email and phone of everyone who ever filed a report.

GetReport raises PostNotFound rather than NotAuthorized for non-public posts: a 403 would confirm the post exists and leak the moderation queue.

Refs: backend_lld.md 8.3, 8.4" -m "$CO"

# 11 ── reports: moderation
git add backend/core/application/reports/moderation.py
git commit -m "feat(reports): add approve, reject, hide and unhide" -m "Note what is absent: any point logic. Points derive from Post.status (DEC-2), so these use cases move one field and the leaderboard follows. No award, no reversal, no cascade to keep in sync.

Reject soft-deletes (the legacy code dropped the row), preserving the audit trail and stopping resubmission gaming. Image deletion and email happen after commit: an external failure must not undo a moderation decision that already committed.

PostModerationLog is an audit trail for humans and is NEVER an input to point calculation (DEC-4).

Refs: backend_lld.md 7.3; DEC-2, DEC-4, DEC-6" -m "$CO"

# 12 ── engagement: likes
git add backend/core/application/engagement/likes.py
git commit -m "feat(engagement): add like and unlike" -m "Anonymous callers may like — recorded, counted and displayed — but the like awards nothing to anyone, including the post owner (DEC-1).

No check-then-act: uniqueness is the database's job via a partial unique index, and a read-first guard would let concurrent double-likes through. Self-likes are refused outright.

Refs: backend_lld.md 7.2, 9.3; DEC-1" -m "$CO"

# 13 ── engagement: feedback & contact messages
git add backend/core/application/engagement/submissions.py
git commit -m "feat(engagement): add feedback and contact message submission" -m "Both are greenfield, not a migration: the legacy feedback() view only rendered a template and never handled POST, and the Rate document had no fields at all — its form submitted into the void.

Both accept anonymous submissions; authenticated ones take identity from the profile.

Refs: backend_lld.md 4.2" -m "$CO"

# 14 ── accounts: registration & OTP
git add backend/core/application/accounts/dto.py backend/core/application/accounts/registration.py
git commit -m "feat(accounts): add registration and OTP verification" -m "Ports the legacy flow with two corrections:

- is_active and is_verified are separated. The legacy model defaulted is_active=False and used it to gate unverified accounts, conflating 'not yet verified' with 'banned'. Now is_verified gates sign-in and is_active means not banned.
- OTP expiry is checked on read. The legacy TTL index was a Mongo feature; Postgres has none, so correctness must never depend on a cleanup job running.

OTP codes use secrets, not random: they guard account takeover. ResendOTP returns silently for unknown usernames to avoid account enumeration.

Refs: backend_lld.md 9.1, 9.4" -m "$CO"

# 15 ── accounts: login, refresh, logout
git add backend/core/application/accounts/authentication.py
git commit -m "feat(accounts): add login, token refresh and logout" -m "Sessions are gone: the legacy flow set request.session['user_id'] plus a remember_me cookie. Tokens replace both.

Logout is real — revoking the refresh token is server-side state, without which logout would only mean 'the client forgot'.

Verification and ban checks run only AFTER the password check: answering 'not verified' to a wrong password would confirm the account exists. RefreshToken re-checks the user, so a user banned mid-session cannot refresh their way back in.

Refs: backend_lld.md 8.1" -m "$CO"

# 16 ── accounts: password reset
git add backend/core/application/accounts/password.py
git commit -m "feat(accounts): add password reset via OTP" -m "RequestPasswordReset returns silently for unknown usernames — distinguishing would leak which accounts exist.

Refs: backend_lld.md 10" -m "$CO"

# 17 ── accounts: profile & admin user management
git add backend/core/application/accounts/profile.py backend/core/application/accounts/administration.py
git commit -m "feat(accounts): add profile update and admin user management" -m "Username, email and role are not self-editable: email changes need re-verification, role changes are an admin action.

SetUserRole refuses self-modification — without it the last admin can demote themselves and lock everyone out. Staff cannot deactivate an admin.

Refs: backend_lld.md 7, 10" -m "$CO"

# 18 ── content: contact page
git add backend/core/application/content/contact_page.py
git commit -m "feat(content): add admin-editable contact page" -m "Structured fields rather than one JSON blob. Postgres would happily store a blob, but nothing would validate it and every consumer would re-derive the shape; since this is an admin form, validation belongs server-side.

Singleton — there is exactly one contact page.

Refs: backend_lld.md 4.2, 11.4" -m "$CO"

# 19 ── scoring: leaderboard & contribution
git add backend/core/application/scoring/leaderboard.py
git commit -m "feat(scoring): add leaderboard and contribution" -m "Both delegate calculation to LeaderboardRepository — the strategy port. The use case only chooses the period window and supplies active rules, so swapping SQL for ORM or NoSQL never touches this file.

Rules are read per request: deactivating a rule takes effect immediately and retroactively (DEC-2 / POL-1 — announce before changing).

Replaces the legacy contribution view, which hardcoded 'every 5 points = 1 level' and zeroed reviews_written and friends_referred.

Refs: backend_lld.md 5.4, 5.5" -m "$CO"

# 20 ── test fakes
git add backend/tests/fakes/system.py backend/tests/fakes/repositories.py backend/tests/fakes/seed.py \
        backend/tests/conftest.py
git commit -m "test(fakes): add in-memory adapters and rule seed data" -m "These are what let the use-case suite run with no database — the B0 acceptance test. conftest.py imports no Django, configures no settings and opens no connection; if it ever needs to, the hexagon has sprung a leak.

InMemoryLeaderboardRepository delegates to core.domain.points: the same reference implementation the contract suite will check the production SQL against.

The in-memory engagement repo mirrors the partial unique index — one like per user per post, comments unconstrained, anonymous rows unconstrained (nothing identifies them, which is exactly why they earn nothing).

NOTE: DEFAULT_LEVEL_RULES thresholds are a PLACEHOLDER needing a product decision. The legacy 'every 5 points = 1 level' is meaningless now one approved post is worth 100.

Refs: backend_lld.md 2.1, 5.2, 12" -m "$CO"

# 21 ── domain tests
git add backend/tests/unit/domain/test_points.py backend/tests/unit/domain/test_periods.py
git commit -m "test(domain): cover point rules and period boundaries" -m "41 tests, no database, no Django, no network. The executable form of LLD 5.3 and the B0 exit criteria.

Proven green: anonymous like awards nobody; self-like awards zero to both sides; likes on pending/hidden posts award nothing; hiding an approved post strips its points AND its likes' points; un-hiding restores them; inactive rules pay zero but still count; rule changes are retroactive (DEC-2); posts bucket by approval date (DEC-3); week boundaries land at Dhaka midnight, not UTC.

Refs: backend_lld.md 5.3, 5.4, 12" -m "$CO"

# 22 ── application tests
git add backend/tests/unit/application/test_submit_report.py backend/tests/unit/application/test_likes.py \
        backend/tests/unit/application/test_moderation.py
git commit -m "test(application): cover submission, likes and moderation" -m "35 tests. Highlights:

- authenticated submit ignores client-supplied name/email/phone (spoofing guard)
- a failed insert deletes the orphaned Drive upload
- one like per user per post; anonymous likes are NOT deduplicated, which is precisely why DEC-1 makes them worth zero
- unhide preserves the original approved_at, so it cannot shift the leaderboard week
- end-to-end proof of DEC-2: hide/unhide round-trips a score 103 -> 0 -> 103 with no point code in any moderation use case

Refs: backend_lld.md 7.1, 7.2, 7.3, 12" -m "$CO"

# 23 ── docs
git add documents/backend_implementation_plan.md documents/b0_implementation_report.md documents/b0_commits.md
git commit -m "docs: add backend implementation plan and B0 report" -m "The plan covers milestones B0-B7 with credential gates: only DATABASE_URL is a hard blocker (B1); Mailjet and Drive sit behind ports and are stubbed by fakes.

The B0 report records verified exit criteria, findings, deviations from the LLD, and the open product decisions (level thresholds, week start day).

Refs: backend_lld.md 14" -m "$CO"

echo
echo "✅ done — $(git rev-list --count HEAD ^HEAD~23) commits created"
git log --oneline -23
git status --short
```

Expect `git status` to be clean afterwards (`backend_old/` and `backend/.venv/` are ignored).

---

## 1–23. The same commits, individually

Run every block from the **repo root** (`plastickothay_dev/`), in order. Each block is one
commit: `git add` then `git commit`. Verify with `git status` at the end.

> `backend/.venv/` is already covered by `.gitignore` and will not be staged.
> `backend_old/` is gitignored on purpose — it stays local as reference and never lands here.

Ordering rule: code lands before the tests that exercise it, so no commit is left with a
red suite. Domain → ports → application → fakes → tests → docs.

---

## 1. Scaffold & tooling

```bash
git add backend/pyproject.toml \
        backend/core/__init__.py \
        backend/core/domain/__init__.py \
        backend/core/ports/__init__.py \
        backend/core/application/__init__.py \
        backend/core/application/accounts/__init__.py \
        backend/core/application/reports/__init__.py \
        backend/core/application/engagement/__init__.py \
        backend/core/application/content/__init__.py \
        backend/core/application/scoring/__init__.py \
        backend/tests/__init__.py \
        backend/tests/fakes/__init__.py \
        backend/tests/unit/__init__.py \
        backend/tests/unit/domain/__init__.py \
        backend/tests/unit/application/__init__.py \
        backend/tests/contract/__init__.py

git commit -m "chore(backend): scaffold hexagonal skeleton and dev tooling" -m "Creates the core/ (domain, ports, application) and tests/ tree for the DRF rewrite, alongside the legacy code which stays untouched until B7.

Adds pytest, ruff and import-linter config. The import-linter contracts are the load-bearing part: they forbid core/ from importing django, rest_framework, psycopg, google, mongoengine, or anything in adapters/api/config. Without mechanical enforcement the boundary erodes silently and the DB port becomes decorative.

Refs: backend_lld.md 2.1, 3" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 2. Domain — identity, errors, value objects

```bash
git add backend/core/domain/ids.py \
        backend/core/domain/errors.py \
        backend/core/domain/value_objects.py

git commit -m "feat(domain): add identity types, error tree and value objects" -m "Replaces the magic numbers scattered through the legacy code: status=1 becomes PostStatus.APPROVED, user_type=3 becomes Role.USER. Adds HIDDEN as a status distinct from REJECTED (hide keeps the image, reject deletes it).

Every DomainError carries a stable code that the API exception handler maps to one HTTP status in exactly one place. GeoPoint validates its own range.

Refs: backend_lld.md 4.1, 4.3, 8.5" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 3. Domain — entities

```bash
git add backend/core/domain/entities.py

git commit -m "feat(domain): add entities as framework-free dataclasses" -m "Plain dataclasses with no .save() and no ORM. The persistence adapter will map between these and Django models. If this module ever imports Django, the DB port is fiction.

Post carries reporter (always present) and reporter_id (None => anonymous), which is the entire anonymous/authenticated split. User.as_reporter() exists so authenticated submissions take contact details from the stored profile rather than the request body.

Post.approve() sets approved_at once only: re-approving after a hide must not shift the leaderboard bucket.

Refs: backend_lld.md 2.2, 4.2" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 4. Domain — pagination & read models

```bash
git add backend/core/domain/pagination.py \
        backend/core/domain/read_models.py

git commit -m "feat(domain): add pagination primitives and read models" -m "PostFilter replaces the legacy overloaded filter param (filter=today|severity_3|accepted), which conflated three orthogonal concerns and could not express 'accepted AND severity 3'.

statuses is not a public query parameter: public use cases pin it to APPROVED, only admin use cases pass anything else.

MapMarker is deliberately not a Post. The map wants thousands of thin markers, the feed wants twenty full records; serving both from one query was the legacy mistake.

Refs: backend_lld.md 8.4" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 5. Domain — leaderboard periods

```bash
git add backend/core/domain/periods.py

git commit -m "feat(domain): compute leaderboard period boundaries in Dhaka time" -m "Timestamps are stored UTC, but week/month/year boundaries are computed in Asia/Dhaka. Bucketing in UTC would reset the weekly leaderboard at 06:00 Monday local — mid-morning for every user.

The legacy code mixed datetime.utcnow() and datetime.now(); that is not carried forward. Input and output here are both tz-aware UTC.

Refs: backend_lld.md 5.4" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 6. Domain — point rules

```bash
git add backend/core/domain/points.py

git commit -m "feat(domain): add derived point rules" -m "Points are derived from current state — no ledger, no score table (DEC-2). A score is a function of current post statuses x current engagements x active rules, so hiding a post strips its points AND its likes' points automatically, and un-hiding restores them, with no reversal code anywhere.

Four conditions gate an engagement: actor is authenticated, post is publicly approved, post is attributable, actor is not the owner. Condition 1 is a security control, not a product choice (DEC-1) — an anonymous liker has no stable identity, so no unique constraint can bind them, and paying the owner would let a shell loop print points forever.

This module is the SPECIFICATION. Production uses raw SQL, so these rules live in two places and can drift; the contract suite in tests/contract/ is what will stop that.

Refs: backend_lld.md 5.1, 5.2, 5.3; DEC-1, DEC-2" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 7. Ports — infrastructure

```bash
git add backend/core/ports/clock.py \
        backend/core/ports/unit_of_work.py \
        backend/core/ports/storage.py \
        backend/core/ports/notifications.py \
        backend/core/ports/security.py

git commit -m "feat(ports): add clock, unit-of-work, storage, notification and security ports" -m "UnitOfWork exists because transaction.atomic() is a Django import and cannot appear in core/, but use cases still need to declare all-or-nothing boundaries. Retrofitting transaction boundaries later is miserable.

Clock makes OTP expiry and period boundaries testable without sleep().

ImageStorage takes decoded bytes, never a base64 string: base64 is transport encoding and is decoded at the serializer.

Notifier speaks domain intent (send_otp), not transport. Django's EMAIL_BACKEND is the transport strategy and lives inside the Mailjet adapter — two layers, deliberately.

Refs: backend_lld.md 6" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 8. Ports — repositories

```bash
git add backend/core/ports/repositories.py

git commit -m "feat(ports): add repository ports" -m "Every method accepts and returns domain types — never an ORM model, never a QuerySet. A lazy queryset crossing this boundary would leak persistence semantics into the domain.

LeaderboardRepository is the calculation strategy port: raw Postgres SQL by default, swappable for an ORM or NoSQL implementation without touching any use case.

EngagementRepository.add() must translate the DB's unique-constraint violation into AlreadyLiked rather than checking first — a check-then-act read would let concurrent double-likes through.

Refs: backend_lld.md 6, 7.2" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 9. Reports — submission

```bash
git add backend/core/application/reports/dto.py \
        backend/core/application/reports/submission.py

git commit -m "feat(reports): add report submission for anonymous and authenticated users" -m "The request payload is identical either way; the only difference is whether a token is present. Anonymous submissions trust the body; authenticated submissions take name/email/phone from the stored profile and IGNORE the body, otherwise a logged-in user could attach a stranger's contact details to a report.

The Drive upload is not part of the transaction, so a failed insert would orphan the file forever. Added a compensating delete on failure — this was not in the LLD sketch.

Refs: backend_lld.md 7.1" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 10. Reports — public queries

```bash
git add backend/core/application/reports/queries.py

git commit -m "feat(reports): add public listing, detail, map and description update" -m "Public listing pins statuses to APPROVED in the USE CASE, not the view and never from a query param.

This closes a live leak in the legacy code: posts() defaulted to Post.objects() — every post regardless of status — which combined with the planned serializer exposing email and pN would have published the name, email and phone of everyone who ever filed a report.

GetReport raises PostNotFound rather than NotAuthorized for non-public posts: a 403 would confirm the post exists and leak the moderation queue.

Refs: backend_lld.md 8.3, 8.4" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 11. Reports — moderation

```bash
git add backend/core/application/reports/moderation.py

git commit -m "feat(reports): add approve, reject, hide and unhide" -m "Note what is absent: any point logic. Points derive from Post.status (DEC-2), so these use cases move one field and the leaderboard follows. No award, no reversal, no cascade to keep in sync.

Reject soft-deletes (the legacy code dropped the row), preserving the audit trail and stopping resubmission gaming. Image deletion and email happen after commit: an external failure must not undo a moderation decision that already committed.

PostModerationLog is an audit trail for humans and is NEVER an input to point calculation (DEC-4).

Refs: backend_lld.md 7.3; DEC-2, DEC-4, DEC-6" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 12. Engagement — likes

```bash
git add backend/core/application/engagement/likes.py

git commit -m "feat(engagement): add like and unlike" -m "Anonymous callers may like — recorded, counted and displayed — but the like awards nothing to anyone, including the post owner (DEC-1).

No check-then-act: uniqueness is the database's job via a partial unique index, and a read-first guard would let concurrent double-likes through. Self-likes are refused outright.

Refs: backend_lld.md 7.2, 9.3; DEC-1" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 13. Engagement — feedback & contact messages

```bash
git add backend/core/application/engagement/submissions.py

git commit -m "feat(engagement): add feedback and contact message submission" -m "Both are greenfield, not a migration: the legacy feedback() view only rendered a template and never handled POST, and the Rate document had no fields at all — its form submitted into the void.

Both accept anonymous submissions; authenticated ones take identity from the profile.

Refs: backend_lld.md 4.2" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 14. Accounts — registration & OTP

```bash
git add backend/core/application/accounts/dto.py \
        backend/core/application/accounts/registration.py

git commit -m "feat(accounts): add registration and OTP verification" -m "Ports the legacy flow with two corrections:

- is_active and is_verified are separated. The legacy model defaulted is_active=False and used it to gate unverified accounts, conflating 'not yet verified' with 'banned'. Now is_verified gates sign-in and is_active means not banned.
- OTP expiry is checked on read. The legacy TTL index was a Mongo feature; Postgres has none, so correctness must never depend on a cleanup job running.

OTP codes use secrets, not random: they guard account takeover. ResendOTP returns silently for unknown usernames to avoid account enumeration.

Refs: backend_lld.md 9.1, 9.4" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 15. Accounts — login, refresh, logout

```bash
git add backend/core/application/accounts/authentication.py

git commit -m "feat(accounts): add login, token refresh and logout" -m "Sessions are gone: the legacy flow set request.session['user_id'] plus a remember_me cookie. Tokens replace both.

Logout is real — revoking the refresh token is server-side state, without which logout would only mean 'the client forgot'.

Verification and ban checks run only AFTER the password check: answering 'not verified' to a wrong password would confirm the account exists. RefreshToken re-checks the user, so a user banned mid-session cannot refresh their way back in.

Refs: backend_lld.md 8.1" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 16. Accounts — password reset

```bash
git add backend/core/application/accounts/password.py

git commit -m "feat(accounts): add password reset via OTP" -m "RequestPasswordReset returns silently for unknown usernames — distinguishing would leak which accounts exist.

Refs: backend_lld.md 10" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 17. Accounts — profile & admin user management

```bash
git add backend/core/application/accounts/profile.py \
        backend/core/application/accounts/administration.py

git commit -m "feat(accounts): add profile update and admin user management" -m "Username, email and role are not self-editable: email changes need re-verification, role changes are an admin action.

SetUserRole refuses self-modification — without it the last admin can demote themselves and lock everyone out. Staff cannot deactivate an admin.

Refs: backend_lld.md 7, 10" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 18. Content — contact page

```bash
git add backend/core/application/content/contact_page.py

git commit -m "feat(content): add admin-editable contact page" -m "Structured fields rather than one JSON blob. Postgres would happily store a blob, but nothing would validate it and every consumer would re-derive the shape; since this is an admin form, validation belongs server-side.

Singleton — there is exactly one contact page.

Refs: backend_lld.md 4.2, 11.4" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 19. Scoring — leaderboard & contribution

```bash
git add backend/core/application/scoring/leaderboard.py

git commit -m "feat(scoring): add leaderboard and contribution" -m "Both delegate calculation to LeaderboardRepository — the strategy port. The use case only chooses the period window and supplies active rules, so swapping SQL for ORM or NoSQL never touches this file.

Rules are read per request: deactivating a rule takes effect immediately and retroactively (DEC-2 / POL-1 — announce before changing).

Replaces the legacy contribution view, which hardcoded 'every 5 points = 1 level' and zeroed reviews_written and friends_referred.

Refs: backend_lld.md 5.4, 5.5" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 20. Test fakes

```bash
git add backend/tests/fakes/system.py \
        backend/tests/fakes/repositories.py \
        backend/tests/fakes/seed.py \
        backend/tests/conftest.py

git commit -m "test(fakes): add in-memory adapters and rule seed data" -m "These are what let the use-case suite run with no database — the B0 acceptance test. conftest.py imports no Django, configures no settings and opens no connection; if it ever needs to, the hexagon has sprung a leak.

InMemoryLeaderboardRepository delegates to core.domain.points: the same reference implementation the contract suite will check the production SQL against.

The in-memory engagement repo mirrors the partial unique index — one like per user per post, comments unconstrained, anonymous rows unconstrained (nothing identifies them, which is exactly why they earn nothing).

NOTE: DEFAULT_LEVEL_RULES thresholds are a PLACEHOLDER needing a product decision. The legacy 'every 5 points = 1 level' is meaningless now one approved post is worth 100.

Refs: backend_lld.md 2.1, 5.2, 12" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 21. Domain tests

```bash
git add backend/tests/unit/domain/test_points.py \
        backend/tests/unit/domain/test_periods.py

git commit -m "test(domain): cover point rules and period boundaries" -m "41 tests, no database, no Django, no network. The executable form of LLD 5.3 and the B0 exit criteria.

Proven green: anonymous like awards nobody; self-like awards zero to both sides; likes on pending/hidden posts award nothing; hiding an approved post strips its points AND its likes' points; un-hiding restores them; inactive rules pay zero but still count; rule changes are retroactive (DEC-2); posts bucket by approval date (DEC-3); week boundaries land at Dhaka midnight, not UTC.

Refs: backend_lld.md 5.3, 5.4, 12" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 22. Application tests

```bash
git add backend/tests/unit/application/test_submit_report.py \
        backend/tests/unit/application/test_likes.py \
        backend/tests/unit/application/test_moderation.py

git commit -m "test(application): cover submission, likes and moderation" -m "35 tests. Highlights:

- authenticated submit ignores client-supplied name/email/phone (spoofing guard)
- a failed insert deletes the orphaned Drive upload
- one like per user per post; anonymous likes are NOT deduplicated, which is precisely why DEC-1 makes them worth zero
- unhide preserves the original approved_at, so it cannot shift the leaderboard week
- end-to-end proof of DEC-2: hide/unhide round-trips a score 103 -> 0 -> 103 with no point code in any moderation use case

Refs: backend_lld.md 7.1, 7.2, 7.3, 12" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 23. Docs

```bash
git add documents/backend_implementation_plan.md \
        documents/b0_implementation_report.md \
        documents/b0_commits.md

git commit -m "docs: add backend implementation plan and B0 report" -m "The plan covers milestones B0-B7 with credential gates: only DATABASE_URL is a hard blocker (B1); Mailjet and Drive sit behind ports and are stubbed by fakes.

The B0 report records verified exit criteria, findings, deviations from the LLD, and the open product decisions (level thresholds, week start day).

Refs: backend_lld.md 14" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Verify

```bash
git log --oneline -23
git status                 # expect: clean (backend_old/ and .venv/ ignored)

cd backend
.venv/bin/pytest           # expect: 76 passed
.venv/bin/lint-imports     # expect: 4 kept, 0 broken
.venv/bin/ruff check .     # expect: All checks passed
```

## If you'd rather squash

```bash
git add backend/ documents/backend_implementation_plan.md documents/b0_implementation_report.md documents/b0_commits.md

git commit -m "feat(backend): B0 — hexagonal core with framework-free domain and use cases" -m "Domain entities, ports, and every use case for reports, accounts, engagement, content and scoring, plus in-memory fakes and 76 tests.

Exit criteria verified: pytest passes with Django, psycopg and PostgreSQL all absent; import-linter keeps 4 contracts; ruff clean. That is the proof the hexagon is real rather than decorative.

Points derive from current state (DEC-2), so hiding a post strips its points and its likes' points with no reversal code. Anonymous likes are recorded but award nobody (DEC-1).

Legacy code stays in backend_old/ (gitignored) as reference until B7.

Refs: backend_lld.md; backend_implementation_plan.md" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
