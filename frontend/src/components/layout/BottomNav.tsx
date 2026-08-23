import { Home, Plus, Trophy, User, MoreHorizontal } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'

const tabs = [
  { to: '/', label: 'Home', icon: Home, end: true },
  { to: '/leaderboard', label: 'Board', icon: Trophy },
] as const

const rightTabs = [
  { to: '/me', label: 'Me', icon: User },
  { to: '/more', label: 'More', icon: MoreHorizontal },
] as const

function Tab({
  to,
  label,
  icon: Icon,
  end,
}: {
  to: string
  label: string
  icon: typeof Home
  end?: boolean
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          'flex flex-col items-center gap-1 text-[10.5px] font-bold transition-colors',
          isActive ? 'text-brand' : 'text-ink-3',
        )
      }
    >
      <Icon className="size-6" strokeWidth={2} />
      {label}
    </NavLink>
  )
}

export function BottomNav() {
  const navigate = useNavigate()
  return (
    <nav className="absolute inset-x-0 bottom-0 z-50 grid h-21 grid-cols-5 items-center border-t border-line bg-[color-mix(in_srgb,var(--surface)_92%,transparent)] px-3.5 pb-[env(safe-area-inset-bottom)] backdrop-blur-lg md:hidden">
      <Tab {...tabs[0]} />
      <Tab {...tabs[1]} />

      {/* center FAB */}
      <div className="flex flex-col items-center gap-1.5">
        <button
          type="button"
          aria-label="Report"
          onClick={() => navigate('/report')}
          className="-mt-6 grid size-14 place-items-center rounded-[18px] bg-[linear-gradient(152deg,var(--brand-2),var(--brand-deep))] text-white shadow-[0_12px_26px_-8px_rgba(10,156,116,.6)] active:scale-95"
        >
          <Plus className="size-7" strokeWidth={2.4} />
        </button>
        <span className="text-[10.5px] font-bold text-ink-3">Report</span>
      </div>

      <Tab {...rightTabs[0]} />
      <Tab {...rightTabs[1]} />
    </nav>
  )
}
