import type { ReactNode } from 'react'
import { OfflineBanner } from '@/components/OfflineBanner'

/**
 * On desktop, centre the app in a phone-width frame so it reads as a device.
 * On real mobile (< sm) it becomes full-bleed — the frame chrome disappears.
 */
export function PhoneFrame({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-ground sm:bg-[radial-gradient(1200px_600px_at_50%_-10%,color-mix(in_srgb,var(--brand)_10%,transparent),transparent)]">
      <div
        className="relative flex h-dvh w-full flex-col overflow-hidden bg-ground sm:h-[892px] sm:w-[412px] sm:rounded-[46px] sm:shadow-[0_0_0_11px_#0b0f0e,0_0_0_13px_#1d2725,0_40px_90px_-30px_rgba(0,0,0,.6)]"
      >
        <OfflineBanner />
        {children}
      </div>
    </div>
  )
}
