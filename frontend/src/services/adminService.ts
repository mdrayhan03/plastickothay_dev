import { api } from '@/lib/api'
import type {
  AdminAnalytics,
  AdminMapMarker,
  AdminPost,
  AdminStats,
  AdminUser,
  AdminUserDetail,
  AuditEntry,
  ContactMessage,
  FeedbackItem,
  Page,
  Role,
  SiteConfig,
} from '@/types'

export const adminService = {
  async reviewQueue(params: { status?: string; severity?: number; cursor?: string } = {}) {
    const { data } = await api.get<Page<AdminPost>>('/admin/posts/', { params })
    return data
  },
  async map() {
    const { data } = await api.get<AdminMapMarker[]>('/admin/map/')
    return data
  },
  async analytics() {
    const { data } = await api.get<AdminAnalytics>('/admin/analytics/')
    return data
  },
  /** All Reports — the review-list view accepts repeated ?status= filters. */
  async reports(params: { statuses?: string[]; severity?: number; cursor?: string } = {}) {
    const { data } = await api.get<Page<AdminPost>>('/admin/posts/', {
      params: { status: params.statuses, severity: params.severity, cursor: params.cursor },
      paramsSerializer: { indexes: null },
    })
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
  async userDetail(id: number) {
    const { data } = await api.get<AdminUserDetail>(`/admin/users/${id}/`)
    return data
  },
  async setActive(id: number, is_active: boolean) {
    const { data } = await api.patch<AdminUser>(`/admin/users/${id}/active/`, { is_active })
    return data
  },
  async setRole(id: number, role: Role) {
    const { data } = await api.patch<AdminUser>(`/admin/users/${id}/role/`, { role })
    return data
  },
  async deleteUser(id: number) {
    await api.delete(`/admin/users/${id}/`)
  },
  async audit(params: { cursor?: string; post?: number } = {}) {
    const { data } = await api.get<Page<AuditEntry>>('/admin/audit/', { params })
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
