import { api } from '@/lib/api'

interface LikeResult {
  post_id: number
  likes: number
  liked_by_me: boolean
}

export const engagementService = {
  async like(postId: number) {
    const { data } = await api.post<LikeResult>(`/posts/${postId}/like/`)
    return data
  },
  async unlike(postId: number) {
    const { data } = await api.delete<LikeResult>(`/posts/${postId}/like/`)
    return data
  },
}
