import {
  CheckSquare,
  ChevronDown,
  ExternalLink,
  FileText,
  LayoutGrid,
  LogOut,
  type LucideIcon,
  Menu,
  MessageSquare,
  Moon,
  ScrollText,
  Search,
  Settings,
  Smartphone,
  Star,
  User,
  Users,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LogoMark } from '@/components/Logo'
import { OfflineBanner } from '@/components/OfflineBanner'
import { useAuth } from '@/context/auth-context'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

type NavItem = { to: string; end?: boolean; icon: LucideIcon; label: string }
const groups: { title?: string; items: NavItem[] }[] = [
  {
    items: [
      { to: '/admin', end: true, icon: LayoutGrid, label: 'Dashboard' },
      { to: '/admin/review', icon: CheckSquare, label: 'Review Queue' },
      { to: '/admin/reports', icon: FileText, label: 'All Reports' },
    ],
  },
  {
    title: 'Community',
    items: [
      { to: '/admin/users', icon: Users, label: 'Users' },
      { to: '/admin/messages', icon: MessageSquare, label: 'Messages' },
      { to: '/admin/feedback', icon: Star, label: 'Feedback' },
    ],
  },
  {
    title: 'System',
    items: [
      { to: '/admin/audit', icon: ScrollText, label: 'Audit Log' },
      { to: '/admin/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export function AdminShell() {
  const { user, logout } = useAuth()
  const { toggle } = useTheme()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [menu, setMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenu(false)
    }
    document.addEventListener('click', close)
    return () => document.removeEventListener('click', close)
  }, [])

  const initials = `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`.toUpperCase()

  return (
    <div className="flex min-h-dvh bg-ground text-ink">
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-62 flex-col border-r border-line bg-surface transition-transform lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-center gap-2.5 px-5 py-5 text-brand">
          <LogoMark className="size-6" />
          <span className="font-display text-lg font-extrabold">PK Admin</span>
        </div>
        <nav className="flex-1 overflow-y-auto px-3">
          {groups.map((g, i) => (
            <div key={i}>
              {g.title && (
                <div className="px-3 pb-1.5 pt-3.5 text-[10.5px] font-extrabold uppercase tracking-[0.08em] text-ink-3">
                  {g.title}
                </div>
              )}
              {g.items.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.end}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      'mb-0.5 flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13.5px] font-semibold transition-colors',
                      isActive ? 'bg-brand-soft text-brand-deep' : 'text-ink-2 hover:bg-surface-2',
                    )
                  }
                >
                  <n.icon className="size-[18px]" />
                  {n.label}
                </NavLink>
              ))}
            </div>
          ))}
          <a
            href="/django-admin/"
            className="mt-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13.5px] font-semibold text-ink-3 hover:bg-surface-2"
          >
            <ExternalLink className="size-[18px]" />
            Django admin
          </a>
        </nav>
        <div className="space-y-0.5 border-t border-line p-3">
          <Link
            to="/"
            className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13.5px] font-semibold text-ink-2 hover:bg-surface-2"
          >
            <Smartphone className="size-[18px]" />
            View the app
          </Link>
          <button
            onClick={toggle}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[13.5px] font-semibold text-ink-2 hover:bg-surface-2"
          >
            <Moon className="size-[18px]" />
            Toggle theme
          </button>
        </div>
      </aside>

      {open && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <OfflineBanner />
        <header className="sticky top-0 z-20 flex items-center gap-4 border-b border-line bg-[color-mix(in_srgb,var(--surface)_85%,transparent)] px-5 py-3 backdrop-blur">
          <button className="lg:hidden" onClick={() => setOpen(true)} aria-label="Menu">
            <Menu className="size-5" />
          </button>
          <div className="flex w-80 max-w-[40%] items-center gap-2.5 rounded-xl border border-line bg-surface-2 px-3.5 py-2.5">
            <Search className="size-[17px] text-ink-3" />
            <input
              placeholder="Search reports, users…"
              className="w-full bg-transparent text-[13.5px] outline-none placeholder:text-ink-3"
            />
          </div>
          <div className="relative ml-auto" ref={menuRef}>
            <button
              onClick={() => setMenu((m) => !m)}
              className="flex items-center gap-2.5 border-l border-line pl-3"
            >
              <div className="grid size-9 place-items-center rounded-full bg-[linear-gradient(135deg,var(--brand-2),var(--brand-deep))] text-sm font-extrabold text-white">
                {initials}
              </div>
              <div className="text-left">
                <div className="text-[13px] font-bold leading-tight">
                  {user?.first_name} {user?.last_name}
                </div>
                <div className="text-[10.5px] font-extrabold uppercase tracking-wide text-brand">
                  {user?.role}
                </div>
              </div>
              <ChevronDown className="size-4 text-ink-3" />
            </button>
            {menu && (
              <div className="absolute right-0 top-[calc(100%+12px)] min-w-48 rounded-2xl border border-line bg-surface p-1.5 shadow-[0_12px_32px_-12px_rgba(10,33,28,.3)]">
                <Link to="/admin/settings" className="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-[13.5px] font-semibold hover:bg-surface-2">
                  <User className="size-[17px] text-ink-2" /> My profile
                </Link>
                <Link to="/admin/settings" className="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-[13.5px] font-semibold hover:bg-surface-2">
                  <Settings className="size-[17px] text-ink-2" /> Settings
                </Link>
                <div className="my-1 h-px bg-line" />
                <button
                  onClick={async () => {
                    await logout()
                    navigate('/login')
                  }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-[13.5px] font-semibold text-sev-5 hover:bg-surface-2"
                >
                  <LogOut className="size-[17px]" /> Log out
                </button>
              </div>
            )}
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 p-5 lg:p-7">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
