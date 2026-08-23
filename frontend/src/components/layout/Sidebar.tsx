import { Home, LogIn, LogOut, Moon, MoreHorizontal, Plus, ShieldCheck, Trophy, User } from 'lucide-react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Avatar } from '@/components/Avatar'
import { LogoMark } from '@/components/Logo'
import { useAuth } from '@/context/auth-context'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

const items = [
  { to: '/', end: true, icon: Home, label: 'Home' },
  { to: '/leaderboard', icon: Trophy, label: 'Leaderboard' },
  { to: '/me', icon: User, label: 'My impact' },
  { to: '/more', icon: MoreHorizontal, label: 'More' },
]

const link = ({ isActive }: { isActive: boolean }) =>
  cn(
    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors',
    isActive ? 'bg-brand-soft text-brand-deep' : 'text-ink-2 hover:bg-surface-2',
  )

/** Desktop navigation — replaces the bottom nav from `md` up. Hidden on mobile. */
export function Sidebar() {
  const { user, status, isStaff, logout } = useAuth()
  const { toggle } = useTheme()
  const navigate = useNavigate()

  return (
    <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col gap-1 border-r border-line bg-surface p-4 md:flex">
      <Link to="/" className="flex items-center gap-2.5 px-2 py-3 text-brand">
        <LogoMark className="size-7" />
        <span className="font-display text-lg font-extrabold text-ink">PlasticKothay</span>
      </Link>

      <nav className="flex flex-col gap-1">
        {items.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end} className={link}>
            <n.icon className="size-[20px]" />
            {n.label}
          </NavLink>
        ))}
      </nav>

      <Link
        to="/report"
        className="my-2 flex items-center justify-center gap-2 rounded-[14px] bg-[linear-gradient(152deg,var(--brand-2),var(--brand-deep))] py-3 font-bold text-white shadow-[0_10px_22px_-10px_color-mix(in_srgb,var(--brand)_70%,transparent)]"
      >
        <Plus className="size-5" />
        Report plastic
      </Link>

      {isStaff && (
        <Link
          to="/admin"
          className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-[#6d3ecf] hover:bg-surface-2 dark:text-[#b79cf0]"
        >
          <ShieldCheck className="size-[20px]" />
          Switch to Admin
        </Link>
      )}

      <div className="flex-1" />

      <button
        onClick={toggle}
        className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold text-ink-2 hover:bg-surface-2"
      >
        <Moon className="size-[20px]" />
        Toggle theme
      </button>

      {status === 'authed' && user ? (
        <div className="mt-1 flex items-center gap-2.5 rounded-2xl bg-surface-2 p-2">
          <Avatar name={`${user.first_name} ${user.last_name}`} src={user.avatar_url} className="size-9 text-[13px]" />
          <div className="min-w-0 flex-1">
            <div className="truncate text-[13px] font-bold leading-tight">
              {user.first_name} {user.last_name}
            </div>
            <button
              onClick={async () => {
                await logout()
                navigate('/')
              }}
              className="inline-flex items-center gap-1 text-[11.5px] font-semibold text-ink-3 hover:text-sev-5"
            >
              <LogOut className="size-3.5" /> Log out
            </button>
          </div>
        </div>
      ) : (
        <Link
          to="/login"
          className="mt-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-brand hover:bg-surface-2"
        >
          <LogIn className="size-[20px]" />
          Sign in
        </Link>
      )}
    </aside>
  )
}
