import type { ReactNode } from 'react'

export function TopBar({
  title,
  right,
  bordered = true,
}: {
  title: string
  right?: ReactNode
  bordered?: boolean
}) {
  return (
    <div
      className={`sticky top-0 z-30 flex items-center gap-3 px-4.5 py-3 backdrop-blur-md ${
        bordered ? 'border-b border-line' : ''
      } bg-[color-mix(in_srgb,var(--ground)_82%,transparent)]`}
    >
      <h1 className="font-display text-[21px] font-bold tracking-[-0.02em]">{title}</h1>
      {right && <div className="ml-auto">{right}</div>}
    </div>
  )
}
