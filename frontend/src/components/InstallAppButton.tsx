import { Download } from 'lucide-react'
import { usePWAInstall } from '@/hooks/usePWAInstall'

interface InstallAppButtonProps {
  iconOnly?: boolean
  className?: string
}

export function InstallAppButton({
  iconOnly = false,
  className = '',
}: InstallAppButtonProps) {
  const { canInstall, promptInstall } = usePWAInstall()

  // Hide completely if already installed or browser hasn't fired the install event
  if (!canInstall) return null

  return (
    <button
      type="button"
      onClick={promptInstall}
      aria-label="Install App"
      title="Install App"
      className={
        iconOnly
          ? `inline-flex items-center justify-center rounded-xl p-2.5 text-ink-2 transition hover:bg-surface-2 ${className}`
          : `flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold text-ink-2 transition hover:bg-surface-2 ${className}`
      }
    >
      <Download className="size-[20px] shrink-0" />
      {!iconOnly && <span>Install App</span>}
    </button>
  )
}