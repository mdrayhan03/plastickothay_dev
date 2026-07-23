import { QueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: (count, error) => {
        // Don't retry client errors (4xx) — only transient failures.
        const status = (error as AxiosError).response?.status
        if (status && status >= 400 && status < 500) return false
        return count < 2
      },
    },
  },
})

/** Centralized query keys so invalidation stays consistent across the app. */
export const qk = {
  siteConfig: ['siteConfig'] as const,
  me: ['me'] as const,
  contribution: ['contribution'] as const,
  badges: ['badges'] as const,
  mapMarkers: ['map'] as const,
  posts: (filters?: unknown) => ['posts', filters] as const,
  ownPosts: ['me', 'posts'] as const,
  leaderboard: (period: string) => ['leaderboard', period] as const,
  contactPage: ['contactPage'] as const,
  adminReview: (status: string) => ['admin', 'review', status] as const,
  adminStats: ['admin', 'stats'] as const,
}
