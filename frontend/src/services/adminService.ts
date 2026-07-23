import { api } from '@/lib/api'
import type {
  AdminPost,
  AdminStats,
  AdminUser,
  ContactMessage,
  FeedbackItem,
  Page,
  SiteConfig,
} from '@/types'

export const adminService = {
  async reviewQueue(params: { status?: string; severity?: number; cursor?: string } = {}) {
    const { data } = await api.get<Page<AdminPost>>('/admin/posts/', { params })
    return data
  },
  async approve(id: number, reason = '') {
    const { data } = await api.post<AdminPost>(`/admin/posts/${id}/approve/`, { reason })
    return data
  },
  async reject(id: number, reason = '') {
    const { data } = await api.post<AdminPost>(`/admin/posts/${id}/reject/`, { reason })
    return data
  },
  async hide(id: number) {
    const { data } = await api.post<AdminPost>(`/admin/posts/${id}/hide/`)
    return data
  },
  async unhide(id: number) {
    const { data } = await api.post<AdminPost>(`/admin/posts/${id}/unhide/`)
    return data
  },
  async stats() {
    const { data } = await api.get<AdminStats>('/admin/stats/')
    return data
  },
  async users(params: { cursor?: string } = {}) {
    const { data } = await api.get<Page<AdminUser>>('/admin/users/', { params })
    return data
  },
  async setActive(id: number, is_active: boolean) {
    const { data } = await api.patch<AdminUser>(`/admin/users/${id}/active/`, { is_active })
    return data
  },
  async messages(params: { cursor?: string } = {}) {
    const { data } = await api.get<Page<ContactMessage>>('/contact-messages/', { params })
    return data
  },
  async setMessageStatus(id: number, status: string) {
    const { data } = await api.patch<ContactMessage>(`/contact-messages/${id}/`, { status })
    return data
  },
  async feedback(params: { cursor?: string } = {}) {
    const { data } = await api.get<Page<FeedbackItem>>('/feedback/', { params })
    return data
  },
  async updateSiteConfig(payload: {
    week_start: string
    site_name: string
    tagline: string
    map_lat?: number | null
    map_lon?: number | null
    map_zoom: number
    flags: Record<string, boolean>
  }) {
    const { data } = await api.put<SiteConfig>('/site-config/', payload)
    return data
  },
}
