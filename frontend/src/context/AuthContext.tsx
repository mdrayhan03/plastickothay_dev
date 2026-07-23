/**
 * Auth state — the only client (non-server) state we keep in Context.
 *
 * On boot we call refresh once: the httpOnly cookie (if present) yields a fresh access token
 * and we hydrate the user, so a page reload restores the session even though the in-memory
 * access token was wiped.
 */
import { useEffect, useState, type ReactNode } from 'react'
import { setAccessToken, setOnAuthLost } from '@/lib/api'
import { authService } from '@/services/authService'
import type { AuthUser } from '@/types'
import { AuthContext, type AuthState } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [status, setStatus] = useState<AuthState['status']>('loading')

  useEffect(() => {
    // If refresh fails anywhere in the app, drop to anonymous.
    setOnAuthLost(() => {
      setAccessToken(null)
      setUser(null)
      setStatus('anon')
    })

    // Boot: try to restore a session from the refresh cookie.
    ;(async () => {
      try {
        const { access } = await authService.refresh()
        setAccessToken(access)
        setUser(await authService.me())
        setStatus('authed')
      } catch {
        setStatus('anon')
      }
    })()
  }, [])

  async function login(username: string, password: string) {
    const { access, user } = await authService.login(username, password)
    setAccessToken(access)
    setUser(user)
    setStatus('authed')
  }

  async function logout() {
    try {
      await authService.logout()
    } finally {
      setAccessToken(null)
      setUser(null)
      setStatus('anon')
    }
  }

  const isStaff = user?.role === 'staff' || user?.role === 'admin'

  return (
    <AuthContext.Provider value={{ user, status, login, logout, isStaff }}>
      {children}
    </AuthContext.Provider>
  )
}
