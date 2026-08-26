import {
  ChevronRight,
  Info,
  LogIn,
  LogOut,
  MessageSquare,
  Moon,
  ShieldCheck,
  Star,
} from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { useTheme } from '@/hooks/useTheme'

function Row({
  icon: Icon,
  label,
  to,
  onClick,
  right,
  tone = 'default',
}: {
  icon: typeof Info
  label: string
  to?: string
  onClick?: () => void
  right?: React.ReactNode
  tone?: 'default' | 'admin' | 'danger'
}) {
  const body = (
    <>
      <span
        className={`grid size-9.5 flex-none place-items-center rounded-[11px] ${
          tone === 'admin'
            ? 'bg-[#2b2140] text-[#b79cf0]'
            : tone === 'danger'
              ? 'bg-[color-mix(in_srgb,var(--sev-5)_15%,transparent)] text-sev-5'
              : 'bg-brand-soft text-brand-deep'
        }`}
      >
        <Icon className="size-[19px]" />
      </span>
      <span className={`font-semibold ${tone === 'danger' ? 'text-sev-5' : ''}`}>{label}</span>
      <span className="ml-auto text-ink-3">{right ?? <ChevronRight className="size-[18px]" />}</span>
    </>
  )
  const cls = 'flex items-center gap-3.5 border-b border-line px-4 py-3.5 last:border-b-0'
  if (to)
    return (
      <Link to={to} className={cls}>
        {body}
      </Link>
    )
  return (
    <button type="button" onClick={onClick} className={`${cls} w-full text-left`}>
      {body}
    </button>
  )
}

export function MorePage() {
  const { user, status, isStaff, logout } = useAuth()
  const { toggle } = useTheme()
  const navigate = useNavigate()

  return (
    <>
      <TopBar title="More" />

      <div className="m-4.5 flex items-center gap-3.5 rounded-[20px] bg-[linear-gradient(150deg,var(--brand-2),var(--brand-deep))] p-4 text-white shadow-md">
        {status === 'authed' && user?.avatar_url ? (
          <img src={user.avatar_url} alt="" className="size-13 rounded-full object-cover" />
        ) : (
          <div className="grid size-13 place-items-center rounded-full bg-white/20 text-lg font-extrabold">
            {status === 'authed' && user ? user.first_name[0]?.toUpperCase() : '?'}
          </div>
        )}
        <div className="min-w-0">
          <div className="truncate font-display text-lg font-bold">
            {status === 'authed' && user ? `${user.first_name} ${user.last_name}` : 'Guest'}
          </div>
          <div className="truncate text-[12.5px] opacity-90">
            {status === 'authed' && user ? user.email : 'Not signed in'}
          </div>
        </div>
      </div>

      <div className="mx-4.5 overflow-hidden rounded-[20px] border border-line bg-surface shadow-sm">
        <Row icon={MessageSquare} label="Contact us" to="/contact" />
        <Row icon={Star} label="Send feedback" to="/feedback" />
        <Row icon={Info} label="About PlasticKothay" to="/about" />
        <Row icon={Moon} label="Appearance" onClick={toggle} right={<span className="text-[13px] font-bold text-brand">Toggle</span>} />
      </div>

      {isStaff && (
        <div className="mx-4.5 mt-3 overflow-hidden rounded-[20px] border border-line bg-surface shadow-sm">
          <Row icon={ShieldCheck} label="Switch to Admin" to="/admin" tone="admin" />
        </div>
      )}

      <div className="mx-4.5 mt-3 overflow-hidden rounded-[20px] border border-line bg-surface shadow-sm">
        {status === 'authed' ? (
          <Row
            icon={LogOut}
            label="Log out"
            tone="danger"
            onClick={async () => {
              await logout()
              navigate('/')
            }}
            right={<span />}
          />
        ) : (
          <Row icon={LogIn} label="Sign in" to="/login" />
        )}
      </div>

      <p className="mt-4 text-center text-xs text-ink-3">PlasticKothay · v1.0 · প্লাস্টিক কোথায়?</p>
    </>
  )
}
