# User Portal — Backend TODO

**Status:** planned (build later) · **Companion:** `admin_backend_todo.md`
**Context:** the user-portal React frontend is built against the prototype spec. A couple of
user-facing features are wired and shipping, but degrade gracefully because their backend
doesn't exist yet. This doc is the backend work to make them fully live. Numbering continues
from `admin_backend_todo.md` (which ends at BE-8).

---

## BE-9 · User avatar (profile photo)

**Why:** registration and edit-profile now let a user pick and upload a profile photo. The
frontend downscales it to a ~256px JPEG data URL and sends it as `avatar`, but there's no field
to store it, so it's dropped.

- Add an avatar to `User` — either a stored image (reuse the **Google Drive image storage** the
  reports use: keep `avatar_provider` + `avatar_external_id`, expose a derived `avatar_url`) or a
  simpler `avatar_url` if you host elsewhere. Mirror the report-image approach for consistency.
- Accept `avatar` (base64 data URL) in:
  - `RegisterSerializer` → store on create.
  - `UpdateProfileSerializer` (`PATCH /api/me/`) → replace on change.
- Return `avatar_url` (nullable) from the **MeSerializer**, the **LeaderboardRow** serializer,
  and the public profile (BE-10).
- Validate: image content-type, max size, re-encode server-side; treat missing/blank as "no
  avatar" (the client falls back to an initials avatar).

**Frontend today:** the avatar picker works and submits `avatar` (ignored by the serializer, no
error). Everywhere an avatar shows — More header, leaderboard, public profile — it falls back to
a gradient **initials** circle until `avatar_url` comes back.

---

## BE-10 · Public user profile + that user's posts

**Why:** the leaderboard now links each row to `/u/<id>`, a public profile showing avatar,
username, full name, badges and the user's reports. No public user endpoint exists — the
leaderboard exposes a `user_id` but nothing to fetch a profile or a user's posts.

- `GET /api/users/<id>/` — **public**, privacy-limited. Serialize:
  `id, username, full_name, avatar_url, level, level_title, total_points, posts_approved,
  likes_received, badges: [{ code, name, icon }]`.
  **No email/phone** — this is public. Reuse `LeaderboardRepository.contribution_for` for stats
  and the earned-badges query.
- `GET /api/users/<id>/posts/?cursor=` — **public**, that user's **approved** posts only,
  cursor-paginated **5 per page** (matches the frontend's page size). Same `PublicPostSerializer`
  as the main feed.
- 404 for a non-existent or inactive user.

**Frontend today:** the profile page renders and calls both endpoints with `retry: false`; on
404 it shows a "profiles aren't available yet (BE-10)" state, and the posts list shows a small
pending note. It lights up fully once these ship.

---

## BE-11 · Expose the reporter's user id on public posts

**Why:** a report card and the report detail sheet should link to the author's public profile
(`/u/<id>`), but the public post payload only carries `reporter_name` — there's no user id to
link to. (Anonymous reports have no user, so this is nullable.)

- Add `reporter_id` (nullable) to `PublicPostSerializer` — the reporter's user id, or `null` for
  anonymous/guest reports.
- Keep it to the **id only** on the public serializer; name is already there, and email/phone
  stay admin-only.

**Frontend today:** the feed card and report sheet don't link to the author — only the
leaderboard links to profiles. Once `reporter_id` is present, wiring an author link is a small
frontend change (skip the link when it's `null`).

---

## Summary

| # | Endpoint / field | Public? | Frontend fallback today |
|---|---|---|---|
| BE-9 ✅ | `avatar` on register + `PATCH /me/`, `avatar_url` out | n/a | **Done** — stored via image storage |
| BE-10 ✅ | `GET /api/users/<id>/` + `GET /api/users/<id>/posts/` (5/page) | yes | **Done** — public profile + posts live |
| BE-11 ✅ | `reporter_id` (nullable) on `PublicPostSerializer` | yes | **Done** — exposed (null for anonymous) |

**STATUS: ALL DONE.** BE-9, BE-10 and BE-11 are implemented and tested. Avatars are stored through
the existing `ImageStorage` (Google Drive in prod, local otherwise) as `avatar_provider` +
`avatar_external_id`, with `avatar_url` derived on read. The public profile is read-only (it never
awards badges for the viewed user). Frontend follow-up: the app already sends `avatar` and renders
`avatar_url`/profiles, but the leaderboard rows don't yet return `avatar_url` (they still show
initials) and report cards can now be linked to `/u/<reporter_id>` since `reporter_id` is exposed.

Both are additive. BE-9 should land before or with BE-10 so avatars appear on the profile; until
then everything falls back to initials and pending states, so nothing is broken.
