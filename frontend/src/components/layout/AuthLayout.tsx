import type { ReactNode } from 'react'
import { LogoMark } from '@/components/Logo'

/** Full-screen auth shell — outside the tab bar. Brand header, then the form/children. */
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
    <div className="flex h-full flex-col overflow-y-auto px-6.5">
      <div className="mt-16 text-center">
        <div className="mx-auto grid size-18 place-items-center rounded-[22px] bg-[linear-gradient(150deg,var(--brand-2),var(--brand-deep))] shadow-[0_12px_26px_-8px_rgba(10,156,116,.6)]">
          <LogoMark className="size-9 text-white" />
        </div>
        <h2 className="mt-4 font-display text-2xl font-extrabold tracking-[-0.02em]">{title}</h2>
        {subtitle && <p className="mt-2 text-sm text-ink-2">{subtitle}</p>}
      </div>
      <div className="mt-8">{children}</div>
      {footer && <div className="mt-auto pb-8 pt-6">{footer}</div>}
    </div>
  )
}
