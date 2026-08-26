import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { qk } from '@/lib/queryClient'
import { userService } from '@/services/userService'

export function usePublicProfile(id: number) {
  return useQuery({
    queryKey: qk.userProfile(id),
    queryFn: () => userService.profile(id),
    retry: false,
    enabled: Number.isFinite(id) && id > 0,
  })
}

/** A user's approved posts, paginated 5/page by the backend. */
export function useUserPosts(id: number) {
  return useInfiniteQuery({
    queryKey: qk.userPosts(id),
    queryFn: ({ pageParam }) => userService.posts(id, { cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    retry: false,
    enabled: Number.isFinite(id) && id > 0,
  })
}
