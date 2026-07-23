import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/queryClient'
import { postService, type SubmitReportPayload } from '@/services/postService'

export function useMapMarkers() {
  return useQuery({ queryKey: qk.mapMarkers, queryFn: postService.mapMarkers })
}

export function usePostFeed(severity?: number) {
  return useInfiniteQuery({
    queryKey: qk.posts({ severity }),
    queryFn: ({ pageParam }) => postService.list({ severity, cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  })
}

export function useOwnPosts() {
  return useInfiniteQuery({
    queryKey: qk.ownPosts,
    queryFn: ({ pageParam }) => postService.ownPosts({ cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  })
}

export function useSubmitReport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SubmitReportPayload) => postService.submit(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.mapMarkers })
      qc.invalidateQueries({ queryKey: ['posts'] })
      qc.invalidateQueries({ queryKey: qk.ownPosts })
    },
  })
}
