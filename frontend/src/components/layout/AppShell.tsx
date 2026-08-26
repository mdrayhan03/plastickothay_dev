import { Outlet } from 'react-router-dom'
import { OfflineBanner } from '@/components/OfflineBanner'
import { BottomNav } from './BottomNav'
import { Sidebar } from './Sidebar'

/**
 * The user portal shell. Mobile: a single scrolling column with the bottom tab bar. Desktop
 * (`md`+): a left sidebar + a centred content column with generous side margins. No phone
 * frame, no faux status bar.
 */
export function AppShell() {
  return (
    <div className="flex min-h-dvh bg-ground text-ink">
      <Sidebar />
      <div className="relative flex min-h-dvh min-w-0 flex-1 flex-col">
        <OfflineBanner />
        <div className="scrollbar-none flex-1 overflow-y-auto pb-24 md:pb-10">
          <div className="mx-auto w-full max-w-3xl">
            <Outlet />
          </div>
        </div>
        <BottomNav />
      </div>
    </div>
  )
}
