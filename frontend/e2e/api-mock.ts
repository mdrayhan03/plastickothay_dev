import type { Page, Route } from '@playwright/test'

/** A tiny 1x1 transparent PNG data URL, used as report image_url in mock data. */
const PIXEL =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

export type MockUser = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  role: 'user' | 'staff' | 'admin'
  is_verified: boolean
  avatar_url: string | null
}

export function user(over: Partial<MockUser> = {}): MockUser {
  return {
    id: 1,
    username: 'rahim',
    email: 'rahim@example.com',
    first_name: 'Rahim',
    last_name: 'Uddin',
    phone: '017',
    role: 'user',
    is_verified: true,
    avatar_url: null,
    ...over,
  }
}

function publicPost(id: number, over: Record<string, unknown> = {}) {
  return {
    id,
    reporter_name: 'Rahim Uddin',
    reporter_id: 1,
    severity: 3,
    image_url: PIXEL,
    lat: 23.78,
    lon: 90.4,
    place_name: 'Hatirjheel, Dhaka',
    description: 'Plastic pile near the canal.',
    created: '2026-07-20T10:00:00Z',
    likes: 4,
    liked_by_me: false,
    ...over,
  }
}

function adminPost(id: number, over: Record<string, unknown> = {}) {
  return {
    ...publicPost(id),
    reporter_email: 'rahim@example.com',
    reporter_phone: '017',
    status: 2,
    approved_at: null,
    ...over,
  }
}

const SITE_CONFIG = {
  week_start: 'monday',
  site_name: 'PlasticKothay Dhaka',
  tagline: 'Clean Dhaka',
  logo_url: null,
  map_center: { lat: 23.78, lon: 90.4 },
  map_zoom: 12,
  flags: {},
}

interface Options {
  /** The session user restored on boot; null = anonymous. */
  authed?: MockUser | null
}

/**
 * Route all backend + map traffic to deterministic in-memory responses. Returns a small state
 * handle so a spec can assert what the app sent (e.g. the submitted report).
 */
export async function installApiMock(page: Page, opts: Options = {}) {
  const state = {
    feed: [publicPost(101), publicPost(102, { place_name: 'Buriganga bank' })],
    markers: [
      { id: 101, lat: 23.78, lon: 90.4, severity: 3 },
      { id: 102, lat: 23.75, lon: 90.39, severity: 5 },
    ],
    pending: [adminPost(201), adminPost(202, { severity: 5 })],
    submitted: [] as Record<string, unknown>[],
    approved: [] as number[],
  }
  const authed = opts.authed ?? null

  const json = (route: Route, data: unknown, status = 200) =>
    route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) })

  // Map tiles + reverse geocoding are external — stub them so tests are offline and fast.
  await page.route(/basemaps\.cartocdn\.com/, (r) => r.abort())
  await page.route(/nominatim\.openstreetmap\.org/, (r) => json(r, { address: {} }))

  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.replace(/\/$/, '') // drop trailing slash
    const method = route.request().method()
    const m = (p: string) => path === `/api${p}`

    // --- auth / session ---
    if (m('/auth/refresh')) return authed ? json(route, { access: 't' }) : json(route, {}, 401)
    if (m('/me') && method === 'GET') return authed ? json(route, authed) : json(route, {}, 401)
    if (m('/auth/login')) return json(route, { access: 't', user: authed ?? user() })
    if (m('/auth/logout')) return json(route, { detail: 'ok' })

    // --- public content ---
    if (m('/site-config')) return json(route, SITE_CONFIG)
    if (m('/map/posts')) return json(route, state.markers)
    if (m('/posts') && method === 'GET')
      return json(route, { results: state.feed, next_cursor: null })
    if (m('/posts') && method === 'POST') {
      const body = route.request().postDataJSON()
      state.submitted.push(body)
      return json(route, publicPost(999, { place_name: body.place_name ?? '' }), 201)
    }
    if (/\/api\/posts\/\d+$/.test(path) && method === 'GET')
      return json(route, state.feed[0] ?? publicPost(101))
    if (/\/api\/posts\/\d+\/like$/.test(path))
      return json(route, { post_id: 101, likes: 5, liked_by_me: method === 'POST' })

    // --- scoring ---
    if (m('/leaderboard')) return json(route, { period: 'week', results: [], next_cursor: null })
    if (m('/me/contribution'))
      return json(route, {
        total_points: 0, posts_approved: 0, likes_received: 0, likes_given: 0,
        level: 1, level_title: 'Newcomer', points_to_next_level: 100, progress_percentage: 0,
        referrals: 0,
      })
    if (m('/me/badges')) return json(route, [])
    if (m('/me/posts')) return json(route, { results: [], next_cursor: null })

    // --- admin ---
    if (m('/admin/posts') && method === 'GET') {
      const status = url.searchParams.get('status') ?? 'pending'
      const items = status === 'pending' ? state.pending.filter((p) => !state.approved.includes(p.id as number)) : []
      return json(route, { results: items, next_cursor: null })
    }
    const approveMatch = path.match(/\/api\/admin\/posts\/(\d+)\/approve$/)
    if (approveMatch) {
      state.approved.push(Number(approveMatch[1]))
      return json(route, adminPost(Number(approveMatch[1]), { status: 1 }))
    }
    if (m('/admin/stats'))
      return json(route, { pending: 2, approved: 5, hidden: 1, rejected: 0, total: 8 })
    if (m('/admin/map')) return json(route, state.markers.map((mk) => ({ ...mk, status: 1 })))
    if (m('/admin/analytics'))
      return json(route, {
        over_time: [{ week: '2026-07-13', submitted: 3, approved: 2 }],
        active_users: 4,
      })
    if (m('/admin/audit')) return json(route, { results: [], next_cursor: null })
    if (m('/admin/users')) return json(route, { results: [], next_cursor: null })
    if (m('/contact-messages')) return json(route, { results: [], next_cursor: null })
    if (m('/feedback')) return json(route, { results: [], next_cursor: null })

    // Anything unhandled: empty 200 rather than a hung request.
    return json(route, {})
  })

  return state
}
