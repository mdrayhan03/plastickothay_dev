import { ChevronLeft } from 'lucide-react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

export function TopBar({
  title,
  right,
  back = false,
  bordered = true,
}: {
  title: string
  right?: ReactNode
  back?: boolean
  bordered?: boolean
}) {
  const navigate = useNavigate()
  return (
    <div
      className={`sticky top-0 z-30 flex items-center gap-2 px-4.5 py-3 backdrop-blur-md ${
        bordered ? 'border-b border-line' : ''
      } bg-[color-mix(in_srgb,var(--ground)_82%,transparent)]`}
    >
      {back && (
        <button
          type="button"
          onClick={() => navigate(-1)}
          aria-label="Go back"
          className="-ml-2 grid size-9 place-items-center rounded-full text-ink hover:bg-surface-2"
        >
          <ChevronLeft className="size-6" />
        </button>
      )}
      <h1 className="font-display text-[21px] font-bold tracking-[-0.02em]">{title}</h1>
      {right && <div className="ml-auto">{right}</div>}
    </div>
  )
}
