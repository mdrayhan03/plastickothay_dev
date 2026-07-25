/**
 * Axios instance + auth interceptors.
 *
 * Access token lives in a module variable (memory) - never localStorage, so XSS can't read
 * it. The refresh token is the backend's httpOnly cookie, sent automatically. On a 401 we
 * refresh once and retry; concurrent 401s queue behind a single in-flight refresh.
 */
import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'
import type { RefreshResponse } from '@/types'

let accessToken: string | null = null
export const setAccessToken = (t: string | null) => {
  accessToken = t
}
export const getAccessToken = () => accessToken

/** Called when refresh fails - the app clears auth and routes to login. Wired by AuthContext. */
let onAuthLost: (() => void) | null = null
export const setOnAuthLost = (fn: () => void) => {
  onAuthLost = fn
}

// Same-origin by default: '/api' is relative, so the Vite proxy (dev) and the Django-served
// build (prod) both keep the app and API on one origin — no CORS, first-party cookie. Only set
// VITE_API_URL to a full URL for a split-origin deploy (which also needs CORS + CSRF_TRUSTED_
// ORIGINS on the backend and SameSite=None;Secure on the refresh cookie).
const API_BASE = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // send the httpOnly refresh cookie
  headers: { 'Content-Type': 'application/json' },
})

// Bare client for refresh, so it never triggers the interceptor's retry loop.
const bare = axios.create({ baseURL: API_BASE, withCredentials: true })

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

// --- single-flight refresh with a waiter queue ---
let refreshing: Promise<string> | null = null

async function refreshAccess(): Promise<string> {
  if (!refreshing) {
    refreshing = bare
      .post<RefreshResponse>('/auth/refresh/')
      .then((r) => {
        setAccessToken(r.data.access)
        return r.data.access
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

type RetriableConfig = AxiosRequestConfig & { _retried?: boolean }

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const status = error.response?.status
    const isRefreshCall = original?.url?.includes('/auth/refresh/')

    if (status === 401 && original && !original._retried && !isRefreshCall) {
      original._retried = true
      try {
        const token = await refreshAccess()
        original.headers = { ...original.headers, Authorization: `Bearer ${token}` }
        return api(original)
      } catch {
        setAccessToken(null)
        onAuthLost?.()
      }
    }
    return Promise.reject(error)
  },
)

/** Extract the backend's error envelope message, with a sensible fallback. */
export function apiErrorMessage(err: unknown, fallback = 'Something went wrong.'): string {
  const e = err as AxiosError<{ error?: { message?: string } }>
  return e?.response?.data?.error?.message ?? fallback
}
