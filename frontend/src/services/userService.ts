import { api } from '@/lib/api'
import type { Page, PublicPost, PublicProfile } from '@/types'

/** Public, privacy-limited views of any user (endpoints BE-10, pending). */
export const userService = {
  async profile(id: number) {
    const { data } = await api.get<PublicProfile>(`/users/${id}/`)
    return data
  },
  async posts(id: number, params: { cursor?: string } = {}) {
    // Backend paginates approved posts at 5/page for the profile.
    const { data } = await api.get<Page<PublicPost>>(`/users/${id}/posts/`, { params })
    return data
  },
}
