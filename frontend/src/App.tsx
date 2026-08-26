import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Splash } from '@/components/layout/Splash'
import { useAuth } from '@/context/auth-context'
import { UserPortal } from '@/portals/UserPortal'

// The admin portal (with Recharts) is staff-only - split it out of the user bundle.
const AdminPortal = lazy(() =>
  import('@/portals/AdminPortal').then((m) => ({ default: m.AdminPortal })),
)

export default function App() {
  const { status } = useAuth()
  if (status === 'loading')
    return (
      <div className="grid min-h-dvh place-items-center bg-ground">
        <Splash />
      </div>
    )

  return (
    <Routes>
      <Route
        path="/admin/*"
        element={
          <Suspense fallback={<div className="min-h-dvh bg-ground" />}>
            <AdminPortal />
          </Suspense>
        }
      />
      <Route path="/*" element={<UserPortal />} />
    </Routes>
  )
}
