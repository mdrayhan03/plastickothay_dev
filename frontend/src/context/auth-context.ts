import { createContext, useContext } from 'react'
import type { AuthUser } from '@/types'
import type { OAuthProvider } from '@/services/oauthProviderService'

export interface AuthState {
  user: AuthUser | null
  status: 'loading' | 'authed' | 'anon'
  login: (username: string, password: string) => Promise<void>
  loginWithOAuth: (provider: OAuthProvider, code: string, redirect_uri: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: AuthUser) => void
  isStaff: boolean
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
