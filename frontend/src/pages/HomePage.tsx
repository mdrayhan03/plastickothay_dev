import { Bell, MapPin, Moon, Sun } from 'lucide-react'
import { useAuth } from '@/context/auth-context'
import { useSiteConfig } from '@/hooks/useSiteConfig'
import { useTheme } from '@/hooks/useTheme'

/**
 * F0 home. Real map + feed arrive in F2 — for now this proves the foundation:
 * the site-config boot fetch, auth status, and the theme toggle all work.
 */
export function HomePage() {
  const { data: config } = useSiteConfig()
  const { user, status } = useAuth()
  const { theme, toggle } = useTheme()

  return (
    <>
      <div className="flex items-center justify-between px-4.5 pb-2 pt-3.5">
        <div>
          <div className="text-[13px] font-semibold text-ink-2">
            {status === 'authed' && user ? `Welcome, ${user.first_name} 👋` : 'Welcome 👋'}
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 font-display text-[22px] font-bold tracking-[-0.02em]">
            <MapPin className="size-[18px] text-brand" />
            Dhaka
          </div>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={toggle}
            aria-label="Toggle theme"
            className="grid size-10 place-items-center rounded-[13px] bg-surface text-ink shadow-sm active:scale-95"
          >
            {theme === 'dark' ? <Sun className="size-5" /> : <Moon className="size-5" />}
          </button>
          <button
            type="button"
            aria-label="Notifications"
            className="grid size-10 place-items-center rounded-[13px] bg-surface text-ink shadow-sm active:scale-95"
          >
            <Bell className="size-5" />
          </button>
        </div>
      </div>

      <div className="mx-4.5 mt-2 rounded-3xl border border-line bg-surface p-6 text-center shadow-sm">
        <div className="font-display text-2xl font-extrabold text-brand">
          {config?.site_name ?? 'PlasticKothay'}
        </div>
        <div
          className="mt-1 text-sm font-bold text-brand"
          style={{ fontFamily: 'var(--font-bengali)' }}
        >
          প্লাস্টিক কোথায়?
        </div>
        <p className="mt-3 text-sm text-ink-2">
          {config?.tagline || 'Map plastic pollution. Clean up your city, together.'}
        </p>
        <p className="mt-4 text-xs text-ink-3">
          Foundation ready — the live map and report feed arrive in F2.
        </p>
      </div>
    </>
  )
}
