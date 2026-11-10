import type { ReactNode } from 'react'
import { LogoMark } from '@/components/Logo'

/** Centred auth page — full-bleed on mobile, a centred card on desktop. Brand header + form. */
export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string
  subtitle?: string
  children: ReactNode
  footer?: ReactNode
}) {
  return (
    <div className="flex min-h-dvh flex-col items-center bg-ground px-6.5 py-12 md:justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center">
          <div className="mx-auto grid size-18 place-items-center rounded-[22px] bg-[linear-gradient(150deg,var(--brand-2),var(--brand-deep))] shadow-[0_12px_26px_-8px_rgba(10,156,116,.6)]">
            <LogoMark className="size-9 text-white" />
          </div>
          <h2 className="mt-4 font-display text-2xl font-extrabold tracking-[-0.02em]">{title}</h2>
          {subtitle && <p className="mt-2 text-sm text-ink-2">{subtitle}</p>}
        </div>
        <div className="mt-8">{children}</div>
        {footer && <div className="pt-6">{footer}</div>}
      </div>
    </div>
  )
}
