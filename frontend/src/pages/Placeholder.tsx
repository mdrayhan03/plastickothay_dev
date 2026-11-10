import type { LucideIcon } from 'lucide-react'
import { TopBar } from '@/components/layout/TopBar'

/** F0 placeholder - real content lands in later milestones. Keeps routing testable now. */
export function Placeholder({
  title,
  icon: Icon,
  milestone,
}: {
  title: string
  icon: LucideIcon
  milestone: string
}) {
  return (
    <>
      <TopBar title={title} />
      <div className="flex flex-col items-center justify-center px-8 py-24 text-center">
        <div className="grid size-16 place-items-center rounded-2xl bg-brand-soft text-brand-deep">
          <Icon className="size-7" />
        </div>
        <p className="mt-5 font-display text-lg font-bold">{title}</p>
        <p className="mt-1 text-sm text-ink-2">Coming in {milestone}</p>
      </div>
    </>
  )
}
