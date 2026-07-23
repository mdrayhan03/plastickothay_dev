import { useQuery } from '@tanstack/react-query'
import { Check, Eye, EyeOff, ScrollText, X } from 'lucide-react'
import { qk } from '@/lib/queryClient'
import { adminService } from '@/services/adminService'
import type { ModerationAction } from '@/types'

const actionMeta: Record<ModerationAction, { label: string; icon: typeof Check; color: string }> = {
  approve: { label: 'approved', icon: Check, color: 'var(--brand)' },
  reject: { label: 'rejected', icon: X, color: 'var(--sev-5)' },
  hide: { label: 'hid', icon: EyeOff, color: 'var(--ink-3)' },
  unhide: { label: 'unhid', icon: Eye, color: 'var(--brand)' },
}

export function AuditLog() {
  const { data, isLoading, isError } = useQuery({
    queryKey: qk.adminAudit,
    queryFn: () => adminService.audit(),
    retry: false,
  })
  const entries = data?.results ?? []

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-extrabold">Audit Log</h1>
        <p className="text-sm text-ink-3">Every moderation action, who did it, and when.</p>
      </div>

      {isLoading && <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />}

      {isError && (
        <div className="grid place-items-center rounded-2xl border border-line bg-surface p-14 text-center">
          <ScrollText className="mb-3 size-8 text-ink-3" />
          <div className="font-bold text-ink">Audit endpoint pending</div>
          <p className="mt-1 max-w-sm text-sm text-ink-2">
            The backend already records every moderation action (<code>PostModerationLog</code>); this
            screen lights up once the <b>GET /api/admin/audit/</b> endpoint (BE-1) is built.
          </p>
        </div>
      )}

      {!isLoading && !isError && entries.length === 0 && (
        <p className="rounded-2xl border border-line bg-surface p-10 text-center text-sm text-ink-3">
          No moderation actions recorded yet.
        </p>
      )}

      {entries.length > 0 && (
        <div className="rounded-2xl border border-line bg-surface shadow-sm">
          {entries.map((e) => {
            const m = actionMeta[e.action]
            return (
              <div key={e.id} className="flex items-start gap-3 border-b border-line px-4 py-3 last:border-b-0">
                <span
                  className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-full"
                  style={{ background: `color-mix(in srgb, ${m.color} 16%, transparent)`, color: m.color }}
                >
                  <m.icon className="size-4" />
                </span>
                <div className="min-w-0 flex-1 text-[13px]">
                  <div>
                    <b>{e.admin}</b> {m.label} report <b>#{e.post_id}</b>
                  </div>
                  {e.reason && <div className="mt-0.5 text-ink-2">“{e.reason}”</div>}
                </div>
                <time className="shrink-0 text-[12px] text-ink-3 tnum">{new Date(e.at).toLocaleString()}</time>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
