# Frontend — Pending Tasks

**Status as of the current build:** the frontend app (user PWA + admin portal) is feature-complete
against the F0–F5 plan and the admin portal spec. What remains is listed below.
**Companions:** `admin_backend_todo.md` (BE-0..BE-8), `user_portal_backend_todo.md` (BE-9..BE-11).

Legend: ☐ = pending · frontend items are things we can do without the backend.

---

## 1. Frontend-only (actionable now)

- ☐ **End-to-end test** — a real browser run (Playwright) through the full loop
  (submit report → admin approve → appears on the map). Today: 34 unit/component/MSW tests, no e2e.

## 2. Manual QA (needs a browser / real devices — can't automate here)

- ☐ **PWA / Lighthouse audit** — installability score, "Add to Home Screen" on iOS + Android.
- ☐ **Real-device responsive & safe-area pass** — verify on actual phone sizes and notches.
- ☐ **Accessibility audit** — screen-reader pass + contrast check across all screens.
      (Done already: focus-visible rings, reduced-motion, associated form labels.)

## 3. Deferred by decision (not scheduled)

- ☐ **Notification system + bell** — the Home/notification bell stays a placeholder. Separate feature
      (backend model + endpoints + in-app list). Explicitly deferred.

## 4. Backend-dependent (frontend built, degrades gracefully — unblocks when the endpoint ships)

Nothing to build on the frontend for these until the backend lands; each already has a fallback.

- ☐ **BE-0** admin users API (list / activate / role) — Users screen shows a "needs API" notice.
- ☐ **BE-1** audit log endpoint — Audit screen + dashboard activity show pending states.
- ☐ **BE-2** delete user — button wired, notes pending.
- ☐ **BE-3** admin all-status map — dashboard uses approved-only markers.
- ☐ **BE-4** admin user detail + stats — profile drawer stats read "—".
- ☐ **BE-5** dashboard analytics (over-time, active users) — chart omitted, KPI hidden.
- ☐ **BE-7** tighten site-config write to superuser — client already hides it from staff.
- ☐ **BE-8** `place_name` on reports — sent + displayed with a coordinate fallback.
- ☐ **BE-9** user avatar field — picker works, photo dropped, initials shown until it lands.
- ☐ **BE-10** public profile + user-posts endpoints — profile page shows a pending state.
- ☐ **BE-11** `reporter_id` on public posts — needed before report→author links.

## 5. Optional polish (nice-to-have)

- ☐ **Author links on feed cards / report sheet** — blocked on **BE-11**, then a small FE change
      (skip the link when `reporter_id` is null for anonymous reports).
- ☐ **In-app camera** requires a secure context (HTTPS / localhost) — known web limitation, not a bug.

---

## Admin portal — status

The admin portal frontend is **complete** (shell, dashboard, review queue, all-reports, users,
messages, feedback, audit log, settings, working top-bar search). It has **no frontend-only
pending items**. Everything outstanding there is backend-dependent (BE-0, BE-1, BE-2, BE-3, BE-4,
BE-5, BE-7 above) or the shared manual-QA / e2e items in sections 1–2.
