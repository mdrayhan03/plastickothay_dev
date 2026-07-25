import { severityColor, severityLabel } from '@/lib/severity'
import { statusMeta } from '@/lib/status'
import { cn } from '@/lib/utils'
import type { PostStatus, Role, Severity } from '@/types'

export function StatusChip({ status }: { status: PostStatus }) {
  const m = statusMeta[status]
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold', m.cls)}>
      <span className="size-1.5 rounded-full" style={{ background: m.dot }} />
      {m.label}
    </span>
  )
}

export function SeverityChip({ severity }: { severity: Severity }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold"
      style={{ background: `color-mix(in srgb, ${severityColor[severity]} 16%, transparent)`, color: severityColor[severity] }}
    >
      <span className="size-1.5 rounded-full" style={{ background: severityColor[severity] }} />
      {severityLabel[severity]}
    </span>
  )
}

const roleCls: Record<Role, string> = {
  admin: 'bg-[#efe7fb] text-[#6d3ecf] dark:bg-[#2b2140] dark:text-[#b79cf0]',
  staff: 'bg-brand-soft text-brand-deep',
  user: 'bg-surface-2 text-ink-2',
}

export function RoleChip({ role }: { role: Role }) {
  return (
    <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide', roleCls[role])}>
      {role}
    </span>
  )
}
