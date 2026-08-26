# Admin Portal Plan

**Branch:** `frontend` · **Status:** plan (prototype locked, refinement pending)
**Prototype:** `frontend/ui_ux_admin/index.html` (open in a desktop browser - the visual spec)
**Companion:** `frontend_plan.md`, `frontend_milestones_f0_f5.md`
**GitHub issue:** #20 (Build React Admin Dashboard)

---

## 1. What it is

The **second portal** of the same React app: a **desktop-first** admin console for staff and
admins, living at `/admin`. One build, one deploy - it shares auth, the API client, React
Query, and the design tokens with the user portal, but renders in its own full-width shell
(no phone frame). Regular users never see it; staff reach it via **More → Switch to Admin**,
and land there or in the user portal at will.

**Principle:** the user portal is thumb-first and roomy; the admin portal is **information-first
and dense** - tables, filters, bulk actions, charts. Same brand, opposite density.

A working-but-basic version already shipped in **F4**. This plan is the spec to bring it up to
the prototype.

---

## 2. Design system (from the prototype)

Reuses the locked token system (green = brand/action, gold = reward, severity ramp = status),
both themes. The shifts for a data-dense desktop UI:

- **Layout:** fixed left sidebar (248px) + sticky top bar (search, notifications, user menu) +
  a max-width (1180px) content area.
- **Density:** smaller radii, tables over cards, compact spacing, `tabular-nums` everywhere
  digits align.
- **State encoded as form, not just text:** status chips (pending amber / approved green /
  hidden grey / rejected red), severity chips, so a queue reads at a glance.
- **Semantic status colors are separate from the brand accent** - pending/approved/hidden/
  rejected are their own set.
- **Charts get real care** (Chart.js in the prototype; Recharts in React): area fills, faint
  grids, severity-colored bars, a status doughnut.

---

## 3. Navigation & sections

Sidebar, grouped:

| Group | Item | Screen |
|---|---|---|
| - | **Dashboard** | KPIs, density map, charts, top contributors, activity |
| - | **Review Queue** (count badge) | the daily moderation job |
| - | **All Reports** | every report, any status |
| Community | **Users** | filter, profile drawer, role, activate/delete |
| Community | **Messages** (count badge) | contact-form inbox, triage + email reply |
| Community | **Feedback** | ratings + comments |
| System | **Audit Log** | who moderated what, when |
| System | **Settings** | site config (admin-only) |
| footer | Django admin ↗, View the app, theme toggle | |

Top bar: global search, notifications, and a **user-menu dropdown** (My profile · Settings ·
Log out).

---

## 4. Screen specs

### 4.1 Dashboard
- **KPI row:** Pending review, Approved (7d), Total reports, Active users - each with a trend.
- **Density map (Leaflet):** every report as a severity-colored marker, plus translucent
  **hotspot circles** sized by report density over the busiest areas (Hatirjheel, Buriganga…),
  with a count tooltip. This is the "where is it worst" view.
- **Charts:** reports-over-time (submitted vs approved area), by-status doughnut, by-severity
  bar.
- **Top contributors** (gold points) and a **recent-activity** feed of moderation actions.

### 4.2 Review Queue (the centrepiece)
- Status tabs with counts (Pending / Approved / Hidden / Rejected), severity + time filters.
- **Data table:** row checkbox, thumbnail, reporter, location, severity chip, submitted time,
  quick actions (approve ✓ / reject ✕ / view 👁).
- **Bulk bar** appears on selection: "N selected · Approve all / Reject all".
- **Detail drawer** (slide-in): large photo, mini map, all fields, **admin-only reporter
  contact**, moderation history, and Approve / Reject / Hide actions.

### 4.3 All Reports
Full table, status filter, severity, likes, date. Read + drill into the same drawer.

### 4.4 Users
- **Filter tabs:** All / Admins / Staff / Users, plus an active/inactive filter.
- **Profile drawer** on row click: avatar, contact, verified state, stats (reports/likes/points).
- **Role selector** (User/Staff/Admin) - **changeable by Admin only; Staff cannot** (enforced
  client + server).
- **Activate / Deactivate.**
- **Delete only for inactive users** - the delete action is hidden until a user is deactivated
  (prevents deleting an active member; forces a deliberate two-step).

### 4.5 Messages - triage + email reply (no new backend)
The backend already has the **inbound** path: anyone can `POST /api/contact-messages/`. There
is **no outbound/reply** mechanism, and we are deliberately **not** building one now.
- Admin reads incoming messages, sees sender email/phone, marks status (new / read / replied).
- **Reply opens the admin's own email client** via a `mailto:` link (`Re: <subject>`,
  pre-addressed). Zero backend work.
- The "replied" status is the admin's own tracking flag.
- *(Deferred - Option B: an in-app reply endpoint that sends via Mailjet. Only if reply volume
  ever justifies it.)*

### 4.6 Feedback
Card grid - star rating, comment, author. Read-only (feedback is never public).

### 4.7 Audit Log
Timeline of every moderation action: admin, action (approve/reject/hide/unhide), target report,
reason, timestamp. Surfaces the backend's `PostModerationLog`, which currently has no endpoint.

### 4.8 Settings - admin only
Site-config editor (site name, tagline, week start, map centre/zoom, logo, flags). Marked
**Admin only**. Point/level/badge rules stay in Django admin (linked out) - a deliberate
decision, not a gap.

---

## 5. Permission model

| Capability | Staff | Admin (superuser) |
|---|---|---|
| View admin portal | ✅ | ✅ |
| Moderate reports (approve/reject/hide/unhide) | ✅ | ✅ |
| View users, activate/deactivate | ✅ | ✅ |
| **Change a user's role** | ❌ | ✅ |
| **Delete a user** | ❌ | ✅ (inactive only) |
| Edit site settings | ❌ | ✅ |
| Read messages/feedback, triage | ✅ | ✅ |

Guarded on the client (hide/disable) **and** enforced server-side (the API already gates role
changes to superusers; new endpoints must do the same).

---

## 6. Backend additions this surfaces

Most of the admin is already served by existing endpoints. These are **new** and needed:

| # | Need | Endpoint | Notes |
|---|---|---|---|
| BE-1 | **Audit log list** | `GET /api/admin/audit/` (staff) | reads `PostModerationLog`; paginated; optional `?post=<id>` |
| BE-2 | **Delete a user** | `DELETE /api/admin/users/<id>/` (**superuser**) | only when inactive; soft or hard delete - decide |
| BE-3 | **Admin density coords** | reuse `/api/admin/posts/` or a thin `/api/admin/map/` | dashboard map should include all statuses, not just approved (the public map is approved-only) |
| BE-4 | **User detail + stats** (optional) | `GET /api/admin/users/<id>/` | reports/likes/points for the profile drawer; or compose from existing contribution query |

Already present (no work): review queue, approve/reject/hide/unhide, stats, users list,
set-active, set-role, messages list + status, feedback list, site-config get/put.

**Messages reply is intentionally NOT here** - `mailto:` needs no backend (§4.5).

---

## 7. Current F4 vs this spec (the delta)

F4 shipped a functional baseline. To reach the prototype:

| Area | F4 today | This spec adds |
|---|---|---|
| Dashboard | stat tiles + 1 bar chart | **density map**, 3 charts, top contributors, activity feed |
| Review Queue | card list, per-item actions | **table, bulk select + actions, filters, detail drawer** |
| Users | basic list, activate/deactivate | **filters, profile drawer, role change, delete-if-inactive** |
| Messages | list + status | **mailto reply**, sender links |
| Audit Log | - | **new screen** (needs BE-1) |
| Top bar | name only | **search, notifications, profile/logout dropdown** |
| Feedback | basic list | polished card grid |

---

## 8. Build plan (milestones)

Frontend-first where possible; backend items (BE-*) slot in as their screens need them.

| # | Milestone | Depends on |
|---|---|---|
| **A0** | Shell polish - sidebar sections, top-bar search + notifications + user dropdown (profile/logout), responsive collapse | - |
| **A1** | Dashboard - KPI row, **density map** (BE-3), 3 Recharts, top contributors, activity | BE-3 |
| **A2** | Review Queue - table, filters, **bulk actions**, **detail drawer** (photo, map, history, moderate) | - |
| **A3** | All Reports - table + status filter, drawer reuse | - |
| **A4** | Users - filters, **profile drawer**, role (admin-only), activate/deactivate, **delete inactive** (BE-2, BE-4) | BE-2, BE-4 |
| **A5** | Messages (triage + **mailto reply**) + Feedback grid | - |
| **A6** | Audit Log screen | BE-1 |
| **A7** | Settings admin-only guard + polish; permission-matrix pass over every admin route | - |

Each milestone: keep `npm run build` + lint green, and add a Vitest for any non-trivial logic
(e.g. the bulk-selection reducer, the delete-only-when-inactive guard).

---

## 9. Decision log

| # | Decision | Why |
|---|---|---|
| AD-1 | One app, two shells (phone user portal + desktop admin) split by route | shared auth/API/types; no second codebase |
| AD-2 | Same tokens, **denser** treatment for admin | one brand, right ergonomics per audience |
| AD-3 | Dashboard **density map** with hotspot circles | admins need "where is it worst", not just counts |
| AD-4 | Delete a user **only when inactive** | deliberate two-step; can't nuke an active member |
| AD-5 | Role change + delete + settings = **admin (superuser) only** | staff moderate; admins govern |
| AD-6 | Messages: **triage + `mailto` reply**, no in-app reply | zero backend, frictionless at low volume; Option B deferred |
| AD-7 | Point/level/badge rules stay in **Django admin** | already decided; avoid rebuilding CRUD |
| AD-8 | Audit log surfaces `PostModerationLog` read-only | accountability without a new data model |

---

## 10. Out of scope (for now)

- In-app message reply / two-way inbox / user notifications (Option B) - larger feature.
- User-to-user messaging.
- Rule editing in the React admin (stays in Django admin).
- Bulk endpoints on the backend (bulk actions loop client-side for v1).
- CSV export (nice-to-have; not planned).
