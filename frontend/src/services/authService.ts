import { api } from '@/lib/api'
import type { AuthUser, LoginResponse, RefreshResponse } from '@/types'

export const authService = {
  async login(username: string, password: string) {
    const { data } = await api.post<LoginResponse>('/auth/login/', { username, password })
    return data
  },
  async refresh() {
    const { data } = await api.post<RefreshResponse>('/auth/refresh/')
    return data
  },
  async logout() {
    await api.post('/auth/logout/')
  },
  async me() {
    const { data } = await api.get<AuthUser>('/me/')
    return data
  },
  async register(payload: {
    username: string
    email: string
    first_name: string
    last_name: string
    phone: string
    password: string
  }) {
    await api.post('/auth/register/', payload)
  },
  async verify(username: string, code: number) {
    await api.post('/auth/verify/', { username, code })
  },
}
