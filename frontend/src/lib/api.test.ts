import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { api, getAccessToken, setAccessToken, setOnAuthLost } from './api'

let refreshCount = 0
let refreshShouldFail = false

const server = setupServer(
  http.post('*/api/auth/refresh/', () => {
    refreshCount++
    if (refreshShouldFail) return new HttpResponse(null, { status: 401 })
    return HttpResponse.json({ access: `refreshed-${refreshCount}` })
  }),
  http.get('*/api/protected/', ({ request }) => {
    const auth = request.headers.get('Authorization')
    if (auth?.startsWith('Bearer refreshed-')) return HttpResponse.json({ ok: true })
    return new HttpResponse(null, { status: 401 })
  }),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  refreshCount = 0
  refreshShouldFail = false
  setAccessToken(null)
  setOnAuthLost(() => {})
})
afterAll(() => server.close())

describe('auth interceptor', () => {
  it('refreshes on 401 and retries the original request', async () => {
    setAccessToken('stale')
    const res = await api.get('/protected/')
    expect(res.data).toEqual({ ok: true })
    expect(refreshCount).toBe(1)
    expect(getAccessToken()).toBe('refreshed-1')
  })

  it('shares a single refresh across concurrent 401s (single-flight)', async () => {
    setAccessToken('stale')
    const results = await Promise.all([
      api.get('/protected/'),
      api.get('/protected/'),
      api.get('/protected/'),
    ])
    results.forEach((r) => expect(r.data).toEqual({ ok: true }))
    // Three simultaneous 401s must NOT trigger three refreshes.
    expect(refreshCount).toBe(1)
  })

  it('drops auth and calls onAuthLost when refresh fails', async () => {
    refreshShouldFail = true
    const onLost = vi.fn()
    setOnAuthLost(onLost)
    setAccessToken('stale')

    await expect(api.get('/protected/')).rejects.toBeDefined()
    expect(onLost).toHaveBeenCalledOnce()
    expect(getAccessToken()).toBeNull()
  })

  it('does not try to refresh a failing refresh call itself (no loop)', async () => {
    refreshShouldFail = true
    setAccessToken('stale')
    await expect(api.get('/protected/')).rejects.toBeDefined()
    // One refresh attempt, not an infinite retry loop.
    expect(refreshCount).toBe(1)
  })
})
