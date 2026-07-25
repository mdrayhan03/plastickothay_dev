import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { engagementService } from '@/services/engagementService'
import type { Page, PublicPost } from '@/types'
import { useLike } from './useLike'

vi.mock('@/services/engagementService', () => ({
  engagementService: {
    like: vi.fn(),
    unlike: vi.fn(),
  },
}))

function post(over: Partial<PublicPost> = {}): PublicPost {
  return {
    id: 1,
    reporter_name: 'R',
    reporter_id: null,
    severity: 3,
    image_url: '',
    lat: 0,
    lon: 0,
    description: 'd',
    created: '2026-01-01',
    likes: 5,
    liked_by_me: false,
    ...over,
  }
}

let qc: QueryClient
const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={qc}>{children}</QueryClientProvider>
)

const feedKey = ['posts', { severity: undefined }]
function feed(p: PublicPost) {
  return { pages: [{ results: [p], next_cursor: null } as Page<PublicPost>], pageParams: [undefined] }
}

beforeEach(() => {
  qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  vi.clearAllMocks()
})

describe('useLike (optimistic)', () => {
  it('bumps the count and flips liked_by_me immediately', async () => {
    qc.setQueryData(feedKey, feed(post({ likes: 5, liked_by_me: false })))
    vi.mocked(engagementService.like).mockResolvedValue({ post_id: 1, likes: 6, liked_by_me: true })

    const { result } = renderHook(() => useLike(), { wrapper })
    act(() => {
      result.current.mutate({ post: post({ likes: 5, liked_by_me: false }) })
    })

    // Optimistic: the cache updates before the request resolves.
    await waitFor(() => {
      const data = qc.getQueryData<ReturnType<typeof feed>>(feedKey)
      expect(data?.pages[0].results[0].likes).toBe(6)
      expect(data?.pages[0].results[0].liked_by_me).toBe(true)
    })
    expect(engagementService.like).toHaveBeenCalledWith(1)
  })

  it('rolls back on error', async () => {
    qc.setQueryData(feedKey, feed(post({ likes: 5, liked_by_me: false })))
    vi.mocked(engagementService.like).mockRejectedValue(new Error('boom'))

    const { result } = renderHook(() => useLike(), { wrapper })
    act(() => {
      result.current.mutate({ post: post({ likes: 5, liked_by_me: false }) })
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
    const data = qc.getQueryData<ReturnType<typeof feed>>(feedKey)
    // Reverted to the original 5 / not-liked.
    expect(data?.pages[0].results[0].likes).toBe(5)
    expect(data?.pages[0].results[0].liked_by_me).toBe(false)
  })

  it('unlikes when already liked', async () => {
    qc.setQueryData(feedKey, feed(post({ likes: 6, liked_by_me: true })))
    vi.mocked(engagementService.unlike).mockResolvedValue({ post_id: 1, likes: 5, liked_by_me: false })

    const { result } = renderHook(() => useLike(), { wrapper })
    act(() => {
      result.current.mutate({ post: post({ likes: 6, liked_by_me: true }) })
    })

    await waitFor(() => {
      const data = qc.getQueryData<ReturnType<typeof feed>>(feedKey)
      expect(data?.pages[0].results[0].likes).toBe(5)
      expect(data?.pages[0].results[0].liked_by_me).toBe(false)
    })
    expect(engagementService.unlike).toHaveBeenCalledWith(1)
  })
})
