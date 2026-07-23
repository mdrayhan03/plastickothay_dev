import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'
import { Splash } from './Splash'

/** Guards a route: anonymous users are sent to /login (with a return path). */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <Splash />
  if (status === 'anon')
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <>{children}</>
}

/** Staff/admin-only guard (client-side; the API enforces it too). */
export function StaffRoute({ children }: { children: ReactNode }) {
  const { status, isStaff } = useAuth()
  if (status === 'loading') return <Splash />
  if (status === 'anon') return <Navigate to="/login" replace />
  if (!isStaff) return <Navigate to="/" replace />
  return <>{children}</>
}
