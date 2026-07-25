# Admin Portal — Backend TODO

**Status:** planned (build later) · **Companion:** `admin_portal_plan.md`
**Context:** the React admin portal is built against the prototype spec. Most of it uses
existing endpoints, but a few screens degrade gracefully because these endpoints don't exist
yet. This doc is the backend work to make them fully live.

The frontend already handles the absence of each (empty states / disabled actions / a note),
so shipping these later is non-breaking.

---

## BE-1 · Audit log list endpoint

**Why:** the Audit Log screen surfaces `PostModerationLog` (already a model, written on every
moderation action), but nothing exposes it.

- `GET /api/admin/audit/` — staff/admin, cursor-paginated, newest first.
- Optional `?post=<id>` to scope to one report's history (also feeds the review drawer's
  "moderation history").
- Serialize: `admin` (name), `action`, `post_id`, `reason`, `at`.
- **Adapter note:** `ModerationLogRepository` already has `list_for_post`; add a `list(page)`
  method + a use case + view.

**Frontend today:** the Audit Log screen shows an empty state ("audit endpoint pending"); the
review drawer's history shows only "submitted".

---

## BE-0 · Users list, activate/deactivate, role change (FOUNDATIONAL) ✅ DONE

**Implemented.** `GET /api/admin/users/` (staff, paginated), `PATCH /api/admin/users/<id>/active/`
(staff; forbids self and, for staff, deactivating an admin), `PATCH /api/admin/users/<id>/role/`
(admin only; forbids changing your own role). Use cases already existed in
`core/application/accounts/administration.py`; this added the serializers, views (`UserListView`,
`UserActiveView`, `UserRoleView`) and URLs, plus 12 unit + 11 integration tests (233 total pass).
The list is plain cursor pagination — the admin UI filters by role/active/search client-side, so
no server-side filters were needed.

---

### Original spec

**Why:** the whole Users screen has **no data source** — `api/admin/urls.py` exposes only
`posts/*` and `stats/`. There is no user list, no activate, no role endpoint. (Messages,
feedback and site-config *do* exist, under `api/content/` — those screens are fully live.)

- `GET /api/admin/users/` — staff/admin — cursor-paginated list `(id, name, email, phone,
  role, is_verified, is_active)`, with `?role=` and `?active=` filters and `?q=` search.
- `PATCH /api/admin/users/<id>/active/` — staff/admin — `{ is_active }`.
- `PATCH /api/admin/users/<id>/role/` — **superuser only** — `{ role }`; refuse changing your
  own role and refuse promoting past your own level.
- **Adapter note:** needs a user repository read/list + a use case per action + views, gated by
  `IsStaffOrAdmin` (list/active) and a superuser check (role).

**Frontend today:** the Users screen renders its full UI (filters, table, profile drawer) but
the list query 404s → it shows a "needs the admin users API" notice instead of rows. Activate,
role change and delete are wired and disabled with the same note.

This is the prerequisite for **BE-2** and **BE-4** below (both act on a user that this endpoint
lists).

---

## BE-2 · Delete a user

**Why:** admins can deactivate a user; the spec allows **deleting an inactive** one, but there's
no delete endpoint.

- `DELETE /api/admin/users/<id>/` — **superuser only** (not staff).
- Guard: refuse unless the user is already inactive; refuse self-delete; refuse deleting an
  admin.
- **Decision needed:** soft-delete (set a `deleted_at`, keep for audit) vs hard-delete. Soft is
  safer given reports reference the user (`reporter_user` is `SET_NULL`, so a hard delete
  orphans their reports to anonymous — acceptable, but decide).

**Frontend today:** the delete button shows only for inactive users and, on click, tells the
admin the endpoint is pending.

---

## BE-3 · Admin density map coordinates (all statuses)

**Why:** the dashboard density map should show **all** reports (pending included — that's the
point of triage), but the only marker endpoint (`/api/map/posts/`) is **approved-only** by
design (it's the public map).

- `GET /api/admin/map/` — staff/admin — returns thin markers `(id, lat, lon, severity, status)`
  for all non-deleted reports.
- Lets the dashboard colour by severity AND distinguish pending vs approved, and compute
  hotspot density over everything.

**Frontend today:** the dashboard map uses the public approved-only markers and computes
hotspot circles client-side from those.

---

## BE-4 · User detail with stats

**Why:** the Users profile drawer wants each user's reports/likes/points; the list endpoint
returns only basic fields.

- `GET /api/admin/users/<id>/` — staff/admin — the user plus their `Contribution`
  (reports_approved, likes_received, points) — reuse `LeaderboardRepository.contribution_for`.

**Frontend today:** the profile drawer shows the fields from the list; stats read "—".

---

## BE-5 · Dashboard time-series + active-user count

**Why:** the "Reports over time" chart and the "Active users" KPI need aggregates that don't
exist.

- Extend `GET /api/admin/stats/` (or a new `/api/admin/analytics/`) with:
  - `over_time`: `[{ week, submitted, approved }]` for the last ~8 weeks.
  - `active_users`: count of users active in the period.
- Postgres `date_trunc('week', ...)` grouping; small and cacheable.

**Frontend today:** the dashboard shows the status doughnut and a severity bar (both from data
it already has); the over-time chart is omitted with a note, and Active Users is hidden or
shows total.

---

## BE-7 · Tighten site-config write to superuser

**Why:** the spec makes Settings **admin-only** (§5), and the frontend now hides the editor from
staff — but `PUT /api/site-config/` is currently gated by `IsStaffOrAdmin`, so a staff user could
still write it via the API.

- Change the write permission on `SiteConfigView.put` from `IsStaffOrAdmin` to a superuser check
  (keep GET public).

**Frontend today:** staff see an "Admins only" panel instead of the form; the gap is server-side
only.

---

## BE-8 · `place_name` on reports (reverse-geocoded location label)

**Why:** the report form now reverse-geocodes the pin (Nominatim/OSM, client-side) so the user
confirms a readable label like *"Hatirjheel, Dhaka"*, and sends it as `place_name`. The frontend
already **displays** it (feed card title, admin table, report drawer) with a coordinate fallback,
and already **submits** it — but the backend drops it because the field doesn't exist yet.

- Add `place_name = models.CharField(max_length=255, blank=True, default="")` to `Post` (+ migration).
- Thread it through the hexagon: `Report` entity + `SubmitReport` command, the ORM mapper, the
  input serializer (`SubmitReportSerializer` — accept + validate/trim, optional), and the output
  serializers (`PublicPostSerializer`, `OwnPostSerializer`, `AdminPostSerializer` — return it).
- Keep it **optional** — a report with no name still submits; `lat`/`lon` stay the source of truth.
- Reverse geocoding stays **client-side at submit** (user confirms the name); no server-side
  geocoding on the write path. A backend fallback geocode is possible later but not needed.

**Frontend today:** sends `place_name` (ignored by the serializer, no error) and, on display, falls
back to coordinates whenever it's absent — so nothing regresses before this ships.

---

## Summary

| # | Endpoint | Role | Frontend fallback today |
|---|---|---|---|
| BE-0 ✅ | `GET /api/admin/users/` + `PATCH .../active/` + `PATCH .../role/` | staff (role=**superuser**) | **Done** — Users screen is fully live |
| BE-1 ✅ | `GET /api/admin/audit/` | staff | **Done** — audit trail with admin names |
| BE-2 ✅ | `DELETE /api/admin/users/<id>/` | **superuser** | **Done** — inactive-only, guards enforced |
| BE-3 ✅ | `GET /api/admin/map/` | staff | **Done** — all-status density markers |
| BE-4 ✅ | `GET /api/admin/users/<id>/` | staff | **Done** — user + contribution stats |
| BE-5 ✅ | `GET /api/admin/analytics/` (new endpoint, not on `/stats/`) | staff | **Done** — weekly over-time + active users |
| BE-7 ✅ | tighten `PUT /api/site-config/` to **superuser** | **superuser** | **Done** — `IsAdmin` on write |
| BE-8 ✅ | `place_name` field on `Post` (+ serializers) | — (write via submit) | **Done** — stored + returned |

**STATUS: ALL DONE.** Every admin backend item (BE-0..BE-8) is implemented, tested (275 backend
tests pass), and architecture-clean (import-linter 4 contracts kept). Note BE-5 landed as a new
`GET /api/admin/analytics/` endpoint rather than extending `/api/admin/stats/` — cleaner
separation of counts vs time-series. The over-time chart uses Monday-start weeks (`date_trunc`),
independent of the configured leaderboard week-start.

All are additive and staff/superuser-gated. None block the frontend from shipping; each just
lights up a currently-degraded piece. Each needs a use case + adapter method + view + tests,
consistent with the hexagonal backend.
