# Frontend - Pending Tasks

**Status as of the current build:** the frontend app (user PWA + admin portal) is feature-complete
against the F0–F5 plan and the admin portal spec. What remains is listed below.
**Companions:** `admin_backend_todo.md` (BE-0..BE-8), `user_portal_backend_todo.md` (BE-9..BE-11).

Legend: ☐ = pending · frontend items are things we can do without the backend.

---

## 1. Frontend-only (actionable now)

- ☐ **End-to-end test** - a real browser run (Playwright) through the full loop
  (submit report → admin approve → appears on the map). Today: 34 unit/component/MSW tests, no e2e.

## 2. Manual QA (needs a browser / real devices - can't automate here)

- ☐ **PWA / Lighthouse audit** - installability score, "Add to Home Screen" on iOS + Android.
- ☐ **Real-device responsive & safe-area pass** - verify on actual phone sizes and notches.
- ☐ **Accessibility audit** - screen-reader pass + contrast check across all screens.
      (Done already: focus-visible rings, reduced-motion, associated form labels.)

## 3. Deferred by decision (not scheduled)

- ☐ **Notification system + bell** - the Home/notification bell stays a placeholder. Separate feature
      (backend model + endpoints + in-app list). Explicitly deferred.

## 4. Backend - ✅ ALL DONE (BE-0..BE-11)

Every documented backend endpoint/field is now implemented and tested (275 backend tests pass,
import-linter clean). See `admin_backend_todo.md` and `user_portal_backend_todo.md`. The
previously-degraded admin screens (Users, Audit, delete, all-status map, user stats, analytics)
and user features (avatar, public profiles, `place_name`, `reporter_id`) are all live.

**Follow-ups these unlocked:**
- ✅ Dashboard **over-time chart** wired to `GET /api/admin/analytics/` (+ Active-users KPI, and
      the Recent-activity feed now reads the audit endpoint).
- ✅ Dashboard **density map** switched to `GET /api/admin/map/` (all statuses, not approved-only).
- ✅ **Report cards + detail sheet** link to `/u/<reporter_id>` (skips anonymous reports).
- ✅ **Leaderboard avatars** - backend now returns `avatar_url` on leaderboard rows (BE-12); the
      frontend already rendered it.

## 5. Optional polish (nice-to-have)

- ☐ **In-app camera** requires a secure context (HTTPS / localhost) - known web limitation, not a bug.

---

## Admin portal - status

The admin portal frontend is **complete** (shell, dashboard, review queue, all-reports, users,
messages, feedback, audit log, settings, working top-bar search). It has **no frontend-only
pending items**. Everything outstanding there is backend-dependent (BE-0, BE-1, BE-2, BE-3, BE-4,
BE-5, BE-7 above) or the shared manual-QA / e2e items in sections 1–2.
