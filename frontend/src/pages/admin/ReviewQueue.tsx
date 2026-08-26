import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Eye, EyeOff, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { SeverityChip } from '@/components/admin/Chips'
import { ReportDrawer } from '@/components/admin/ReportDrawer'
import { apiErrorMessage } from '@/lib/api'
import { qk } from '@/lib/queryClient'
import { cn } from '@/lib/utils'
import { adminService } from '@/services/adminService'
import type { AdminPost, ModerationAction } from '@/types'

const TABS = [
  { key: 'pending', label: 'Pending' },
  { key: 'approved', label: 'Approved' },
  { key: 'hidden', label: 'Hidden' },
  { key: 'rejected', label: 'Rejected' },
] as const

type TabKey = (typeof TABS)[number]['key']

/** Which bulk action each tab offers. */
const bulkFor: Record<TabKey, ModerationAction | null> = {
  pending: 'approve',
  approved: 'hide',
  hidden: 'unhide',
  rejected: null,
}

export function ReviewQueue() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<TabKey>('pending')
  const [severity, setSeverity] = useState<number | undefined>()
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [active, setActive] = useState<AdminPost | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: [...qk.adminReview(tab), severity],
    queryFn: () => adminService.reviewQueue({ status: tab, severity }),
  })

  const act = useMutation({
    mutationFn: ({ id, action }: { id: number; action: ModerationAction }) => adminService[action](id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'review'] })
      qc.invalidateQueries({ queryKey: qk.adminStats })
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  })

  const posts = data?.results ?? []

  function switchTab(k: TabKey) {
    setTab(k)
    setSelected(new Set())
  }
  function toggle(id: number) {
    setSelected((s) => {
      const n = new Set(s)
      if (n.has(id)) n.delete(id)
      else n.add(id)
      return n
    })
  }
  function toggleAll() {
    setSelected((s) => (s.size === posts.length ? new Set() : new Set(posts.map((p) => p.id))))
  }
  async function runBulk(action: ModerationAction) {
    const ids = [...selected]
    await Promise.all(ids.map((id) => act.mutateAsync({ id, action })))
    toast.success(`${ids.length} ${action}d`)
    setSelected(new Set())
  }
  function single(id: number, action: ModerationAction) {
    act.mutate({ id, action }, { onSuccess: () => toast.success('Done') })
    setActive(null)
  }

  const bulk = bulkFor[tab]

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-extrabold">Review Queue</h1>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-xl border border-line bg-surface-2 p-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => switchTab(t.key)}
              className={cn(
                'rounded-lg px-3.5 py-2 text-[13px] font-bold transition-colors',
                tab === t.key ? 'bg-surface text-ink shadow-sm' : 'text-ink-2',
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
        <select
          value={severity ?? ''}
          onChange={(e) => setSeverity(e.target.value ? Number(e.target.value) : undefined)}
          className="rounded-xl border border-line bg-surface px-3 py-2.5 text-[13px] font-semibold"
        >
          <option value="">All severities</option>
          {[1, 2, 3, 4, 5].map((s) => (
            <option key={s} value={s}>
              Severity {s}
            </option>
          ))}
        </select>
      </div>

      {bulk && selected.size > 0 && (
        <div className="flex items-center gap-3 rounded-xl border border-brand bg-brand-soft px-4 py-2.5">
          <span className="text-[13px] font-bold text-brand-deep">{selected.size} selected</span>
          <button
            disabled={act.isPending}
            onClick={() => runBulk(bulk)}
            className="ml-auto rounded-lg bg-brand px-3.5 py-1.5 text-[13px] font-bold capitalize text-white disabled:opacity-50"
          >
            {bulk} all
          </button>
          {tab === 'pending' && (
            <button
              disabled={act.isPending}
              onClick={() => runBulk('reject')}
              className="rounded-lg bg-sev-5 px-3.5 py-1.5 text-[13px] font-bold text-white disabled:opacity-50"
            >
              Reject all
            </button>
          )}
        </div>
      )}

      <ReportTable
        posts={posts}
        loading={isLoading}
        selectable={!!bulk}
        selected={selected}
        onToggle={toggle}
        onToggleAll={toggleAll}
        onView={setActive}
        rowActions={(p) => (
          <div className="flex justify-end gap-1.5">
            {p.status === 2 && (
              <>
                <IconBtn title="Approve" onClick={() => single(p.id, 'approve')} tone="brand">
                  <Check className="size-4" />
                </IconBtn>
                <IconBtn title="Reject" onClick={() => single(p.id, 'reject')} tone="danger">
                  <X className="size-4" />
                </IconBtn>
              </>
            )}
            {p.status === 1 && (
              <IconBtn title="Hide" onClick={() => single(p.id, 'hide')}>
                <EyeOff className="size-4" />
              </IconBtn>
            )}
            {p.status === 3 && (
              <IconBtn title="Unhide" onClick={() => single(p.id, 'unhide')} tone="brand">
                <Eye className="size-4" />
              </IconBtn>
            )}
            <IconBtn title="View" onClick={() => setActive(p)}>
              <Eye className="size-4" />
            </IconBtn>
          </div>
        )}
      />

      <ReportDrawer post={active} onClose={() => setActive(null)} onAct={single} busy={act.isPending} />
    </div>
  )
}

function IconBtn({
  children,
  onClick,
  title,
  tone,
}: {
  children: React.ReactNode
  onClick: () => void
  title: string
  tone?: 'brand' | 'danger'
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      className={cn(
        'grid size-8 place-items-center rounded-lg border transition-colors',
        tone === 'brand' && 'border-brand bg-brand-soft text-brand-deep',
        tone === 'danger' && 'border-sev-5/40 text-sev-5 hover:bg-sev-5/10',
        !tone && 'border-line-2 text-ink-2 hover:bg-surface-2',
      )}
    >
      {children}
    </button>
  )
}

/** Shared dense report table - reused by Review Queue and All Reports. */
export function ReportTable({
  posts,
  loading,
  selectable = false,
  selected,
  onToggle,
  onToggleAll,
  onView,
  rowActions,
  extraCol,
}: {
  posts: AdminPost[]
  loading: boolean
  selectable?: boolean
  selected?: Set<number>
  onToggle?: (id: number) => void
  onToggleAll?: () => void
  onView: (p: AdminPost) => void
  rowActions: (p: AdminPost) => React.ReactNode
  extraCol?: { head: string; cell: (p: AdminPost) => React.ReactNode }
}) {
  if (loading) return <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />
  if (posts.length === 0)
    return (
      <p className="rounded-2xl border border-line bg-surface p-12 text-center text-sm text-ink-3">
        Nothing here. 🎉
      </p>
    )

  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-surface shadow-sm">
      <table className="w-full min-w-[720px] text-left text-[13px]">
        <thead>
          <tr className="border-b border-line text-[11px] font-extrabold uppercase tracking-wide text-ink-3">
            {selectable && (
              <th className="w-10 py-3 pl-4">
                <input
                  type="checkbox"
                  checked={!!selected && selected.size === posts.length && posts.length > 0}
                  onChange={onToggleAll}
                  className="size-4 accent-[var(--brand)]"
                />
              </th>
            )}
            <th className="py-3 pl-2">Report</th>
            <th className="py-3">Reporter</th>
            <th className="py-3">Severity</th>
            {extraCol && <th className="py-3">{extraCol.head}</th>}
            <th className="py-3">Submitted</th>
            <th className="py-3 pr-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {posts.map((p) => (
            <tr key={p.id} className="border-b border-line last:border-b-0 hover:bg-surface-2/60">
              {selectable && (
                <td className="py-2.5 pl-4">
                  <input
                    type="checkbox"
                    checked={!!selected?.has(p.id)}
                    onChange={() => onToggle?.(p.id)}
                    className="size-4 accent-[var(--brand)]"
                  />
                </td>
              )}
              <td className="py-2.5 pl-2">
                <button onClick={() => onView(p)} className="flex items-center gap-3 text-left">
                  <img
                    src={p.image_url}
                    alt=""
                    className="size-11 shrink-0 rounded-lg object-cover"
                    style={{ background: 'var(--surface-2)' }}
                  />
                  <span className="min-w-0">
                    <span className="block font-bold text-ink">#{p.id}</span>
                    <span className="block max-w-[200px] truncate text-[12px] text-ink-3">
                      {p.description || 'No description'}
                    </span>
                  </span>
                </button>
              </td>
              <td className="py-2.5">
                <div className="font-semibold text-ink">{p.reporter_name}</div>
                <div className={cn('text-[12px] text-ink-3', !p.place_name && 'tnum')}>
                  {p.place_name || `${p.lat.toFixed(3)}, ${p.lon.toFixed(3)}`}
                </div>
              </td>
              <td className="py-2.5">
                <SeverityChip severity={p.severity} />
              </td>
              {extraCol && <td className="py-2.5">{extraCol.cell(p)}</td>}
              <td className="py-2.5 text-[12.5px] text-ink-2 tnum">
                {new Date(p.created).toLocaleDateString()}
              </td>
              <td className="py-2.5 pr-4">{rowActions(p)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
