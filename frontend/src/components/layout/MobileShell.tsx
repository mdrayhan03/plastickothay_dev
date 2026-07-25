import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'
import { StatusBar } from './StatusBar'

/** The user-portal shell: status bar, a scrollable screen area, and the bottom tab bar. */
export function MobileShell() {
  return (
    <>
      <StatusBar />
      <div className="relative flex-1 overflow-hidden">
        <div className="scrollbar-none h-full overflow-y-auto pb-26">
          <Outlet />
        </div>
      </div>
      <BottomNav />
    </>
  )
}
