import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, X } from 'lucide-react'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { StatusChip } from '@/components/admin/Chips'
import { ReportDrawer } from '@/components/admin/ReportDrawer'
import { apiErrorMessage } from '@/lib/api'
import { qk } from '@/lib/queryClient'
import { cn } from '@/lib/utils'
import { adminService } from '@/services/adminService'
import type { AdminPost, ModerationAction } from '@/types'
import { ReportTable } from './ReviewQueue'

const FILTERS = [
  { key: 'all', label: 'All', statuses: ['pending', 'approved', 'hidden', 'rejected'] },
  { key: 'pending', label: 'Pending', statuses: ['pending'] },
  { key: 'approved', label: 'Approved', statuses: ['approved'] },
  { key: 'hidden', label: 'Hidden', statuses: ['hidden'] },
  { key: 'rejected', label: 'Rejected', statuses: ['rejected'] },
] as const

export function AllReports() {
  const qc = useQueryClient()
  const [filter, setFilter] = useState<(typeof FILTERS)[number]['key']>('all')
  const [active, setActive] = useState<AdminPost | null>(null)
  const [params, setParams] = useSearchParams()
  const q = params.get('q')?.trim().toLowerCase() ?? ''
  const statuses = FILTERS.find((f) => f.key === filter)!.statuses as unknown as string[]

  const { data, isLoading } = useQuery({
    queryKey: qk.adminReports(statuses),
    queryFn: () => adminService.reports({ statuses }),
  })

  const rows = (data?.results ?? []).filter((p) =>
    q
      ? `#${p.id} ${p.reporter_name} ${p.place_name ?? ''} ${p.description}`.toLowerCase().includes(q)
      : true,
  )

  const act = useMutation({
    mutationFn: ({ id, action }: { id: number; action: ModerationAction }) => adminService[action](id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'reports'] })
      qc.invalidateQueries({ queryKey: ['admin', 'review'] })
      qc.invalidateQueries({ queryKey: qk.adminStats })
      toast.success('Done')
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  })
  function single(id: number, action: ModerationAction) {
    act.mutate({ id, action })
    setActive(null)
  }

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-extrabold">All Reports</h1>

      {q && (
        <div className="flex items-center gap-2 text-sm text-ink-2">
          <span>
            Search results for <b className="text-ink">“{params.get('q')}”</b>
          </span>
          <button
            onClick={() => setParams({}, { replace: true })}
            className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2.5 py-1 text-[12px] font-bold text-ink-2 hover:bg-surface"
          >
            <X className="size-3.5" /> Clear
          </button>
        </div>
      )}

      <div className="flex gap-1 rounded-xl border border-line bg-surface-2 p-1 w-fit">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={cn(
              'rounded-lg px-3.5 py-2 text-[13px] font-bold transition-colors',
              filter === f.key ? 'bg-surface text-ink shadow-sm' : 'text-ink-2',
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      <ReportTable
        posts={rows}
        loading={isLoading}
        onView={setActive}
        extraCol={{ head: 'Status', cell: (p) => <StatusChip status={p.status} /> }}
        rowActions={(p) => (
          <div className="flex justify-end">
            <button
              title="View"
              onClick={() => setActive(p)}
              className="grid size-8 place-items-center rounded-lg border border-line-2 text-ink-2 hover:bg-surface-2"
            >
              <Eye className="size-4" />
            </button>
          </div>
        )}
      />

      <ReportDrawer post={active} onClose={() => setActive(null)} onAct={single} busy={act.isPending} />
    </div>
  )
}
