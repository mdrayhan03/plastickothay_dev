import { WifiOff } from 'lucide-react'
import { useOnlineStatus } from '@/hooks/useOnlineStatus'

/** A slim banner shown while the device is offline. Cached content still renders behind it. */
export function OfflineBanner() {
  const online = useOnlineStatus()
  if (online) return null
  return (
    <div
      role="status"
      className="flex items-center justify-center gap-2 bg-ink px-4 py-1.5 text-[12.5px] font-semibold text-[color:var(--surface)]"
    >
      <WifiOff className="size-3.5" />
      You’re offline - showing saved data
    </div>
  )
}
