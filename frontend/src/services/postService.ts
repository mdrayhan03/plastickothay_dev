import { api } from '@/lib/api'
import type { MapMarker, OwnPost, Page, PublicPost } from '@/types'

export interface SubmitReportPayload {
  severity: number
  lat: number
  lon: number
  place_name?: string
  photo: string // base64 data URL
  description?: string
  name?: string
  email?: string
  phone?: string
}

export const postService = {
  async mapMarkers() {
    const { data } = await api.get<MapMarker[]>('/map/posts/')
    return data
  },
  async list(params: { severity?: number; cursor?: string; limit?: number } = {}) {
    const { data } = await api.get<Page<PublicPost>>('/posts/', { params })
    return data
  },
  async get(id: number) {
    const { data } = await api.get<PublicPost>(`/posts/${id}/`)
    return data
  },
  async submit(payload: SubmitReportPayload) {
    const { data } = await api.post<PublicPost>('/posts/', payload)
    return data
  },
  async ownPosts(params: { cursor?: string; limit?: number } = {}) {
    const { data } = await api.get<Page<OwnPost>>('/me/posts/', { params })
    return data
  },
  async updateDescription(id: number, description: string) {
    const { data } = await api.patch<OwnPost>(`/posts/${id}/`, { description })
    return data
  },
}
