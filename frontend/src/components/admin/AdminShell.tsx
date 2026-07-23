import {
  BarChart3,
  CheckSquare,
  ExternalLink,
  LayoutGrid,
  MessageSquare,
  Settings,
  Smartphone,
  Star,
  Users,
} from 'lucide-react'
import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LogoMark } from '@/components/Logo'
import { useAuth } from '@/context/auth-context'
import { cn } from '@/lib/utils'

const nav = [
  { to: '/admin', end: true, icon: LayoutGrid, label: 'Dashboard' },
  { to: '/admin/review', icon: CheckSquare, label: 'Review Queue' },
  { to: '/admin/users', icon: Users, label: 'Users' },
  { to: '/admin/messages', icon: MessageSquare, label: 'Messages' },
  { to: '/admin/feedback', icon: Star, label: 'Feedback' },
  { to: '/admin/settings', icon: Settings, label: 'Settings' },
]

export function AdminShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  return (
    <div className="flex min-h-dvh bg-ground text-ink">
      {/* sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-line bg-surface transition-transform lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-center gap-2 px-5 py-5 text-brand">
          <LogoMark className="size-6" />
          <span className="font-display text-lg font-extrabold">PK Admin</span>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors',
                  isActive ? 'bg-brand-soft text-brand-deep' : 'text-ink-2 hover:bg-surface-2',
                )
              }
            >
              <n.icon className="size-[18px]" />
              {n.label}
            </NavLink>
          ))}
          <a
            href="/django-admin/"
            className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-ink-3 hover:bg-surface-2"
          >
            <ExternalLink className="size-[18px]" />
            Django admin
          </a>
        </nav>
        <div className="border-t border-line p-3">
          <Link
            to="/"
            className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-ink-2 hover:bg-surface-2"
          >
            <Smartphone className="size-[18px]" />
            View the app
          </Link>
        </div>
      </aside>

      {open && <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />}

      {/* main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-line bg-[color-mix(in_srgb,var(--surface)_85%,transparent)] px-5 py-3.5 backdrop-blur">
          <button className="lg:hidden" onClick={() => setOpen(true)} aria-label="Menu">
            <BarChart3 className="size-5" />
          </button>
          <div className="ml-auto flex items-center gap-3">
            <div className="text-right">
              <div className="text-[13px] font-bold leading-tight">
                {user?.first_name} {user?.last_name}
              </div>
              <div className="text-[11px] font-semibold uppercase tracking-wide text-brand">
                {user?.role}
              </div>
            </div>
            <button
              onClick={async () => {
                await logout()
                navigate('/login')
              }}
              className="rounded-lg border border-line-2 bg-surface px-3 py-1.5 text-[13px] font-bold"
            >
              Log out
            </button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 p-5 lg:p-7">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
