import { type InfiniteData, useMutation, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/queryClient'
import { engagementService } from '@/services/engagementService'
import type { Page, PublicPost } from '@/types'

type FeedData = InfiniteData<Page<PublicPost>>

/** Optimistic like/unlike across every cached posts feed and single-post detail query. */
export function useLike() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ post }: { post: PublicPost }) =>
      post.liked_by_me ? engagementService.unlike(post.id) : engagementService.like(post.id),

    onMutate: async ({ post }) => {
      const postKey = qk.post(post.id)
      await Promise.all([
        qc.cancelQueries({ queryKey: ['posts'] }),
        qc.cancelQueries({ queryKey: postKey }),
      ])

      const snapshots = qc.getQueriesData<FeedData>({ queryKey: ['posts'] })
      const postSnapshot = qc.getQueryData<PublicPost>(postKey)

      const patch = (p: PublicPost): PublicPost =>
        p.id === post.id
          ? { ...p, liked_by_me: !p.liked_by_me, likes: p.likes + (p.liked_by_me ? -1 : 1) }
          : p

      for (const [key, data] of snapshots) {
        if (!data) continue
        qc.setQueryData<FeedData>(key, {
          ...data,
          pages: data.pages.map((pg) => ({ ...pg, results: pg.results.map(patch) })),
        })
      }

      if (postSnapshot) {
        qc.setQueryData<PublicPost>(postKey, patch(postSnapshot))
      }

      return { snapshots, postKey, postSnapshot }
    },

    onError: (_e, _v, ctx) => {
      ctx?.snapshots.forEach(([key, data]) => qc.setQueryData(key, data))
      if (ctx?.postSnapshot) {
        qc.setQueryData(ctx.postKey, ctx.postSnapshot)
      }
    },
  })
}