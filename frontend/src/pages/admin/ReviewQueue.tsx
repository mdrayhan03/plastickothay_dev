import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Eye, EyeOff, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { apiErrorMessage } from '@/lib/api'
import { qk } from '@/lib/queryClient'
import { severityClass, severityLabel } from '@/lib/severity'
import { cn } from '@/lib/utils'
import { adminService } from '@/services/adminService'
import type { AdminPost, Severity } from '@/types'

const TABS = [
  { key: 'pending', label: 'Pending' },
  { key: 'approved', label: 'Approved' },
  { key: 'hidden', label: 'Hidden' },
] as const

export function ReviewQueue() {
  const qc = useQueryClient()
  const [status, setStatus] = useState<(typeof TABS)[number]['key']>('pending')
  const { data, isLoading } = useQuery({
    queryKey: qk.adminReview(status),
    queryFn: () => adminService.reviewQueue({ status }),
  })

  const act = useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'approve' | 'reject' | 'hide' | 'unhide' }) =>
      adminService[action](id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'review'] })
      qc.invalidateQueries({ queryKey: qk.adminStats })
      toast.success('Done')
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  })

  const posts = data?.results ?? []

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-extrabold">Review Queue</h1>

      <div className="flex gap-1 rounded-xl border border-line bg-surface-2 p-1 sm:w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setStatus(t.key)}
            className={cn(
              'rounded-lg px-4 py-2 text-sm font-bold transition-colors',
              status === t.key ? 'bg-surface text-ink shadow-sm' : 'text-ink-2',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {isLoading && <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />}
      {!isLoading && posts.length === 0 && (
        <p className="rounded-2xl border border-line bg-surface p-10 text-center text-sm text-ink-3">
          Nothing here. 🎉
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {posts.map((post) => (
          <ReviewCard key={post.id} post={post} status={status} onAct={act.mutate} busy={act.isPending} />
        ))}
      </div>
    </div>
  )
}

function ReviewCard({
  post,
  status,
  onAct,
  busy,
}: {
  post: AdminPost
  status: string
  onAct: (v: { id: number; action: 'approve' | 'reject' | 'hide' | 'unhide' }) => void
  busy: boolean
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-sm">
      <img src={post.image_url} alt="" className="h-40 w-full object-cover" style={{ background: 'var(--surface-2)' }} />
      <div className="space-y-2 p-4">
        <div className="flex items-center justify-between">
          <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-bold text-white', severityClass[post.severity as Severity])}>
            {severityLabel[post.severity as Severity]}
          </span>
          <span className="text-xs font-semibold text-ink-3">#{post.id}</span>
        </div>
        <p className="line-clamp-2 text-sm text-ink-2">{post.description}</p>
        <div className="rounded-lg bg-surface-2 p-2.5 text-[12px] text-ink-2">
          <div className="font-bold text-ink">{post.reporter_name}</div>
          <div>{post.reporter_email}</div>
          <div>{post.reporter_phone}</div>
        </div>
        <div className="flex gap-2 pt-1">
          {status === 'pending' && (
            <>
              <button disabled={busy} onClick={() => onAct({ id: post.id, action: 'approve' })} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-brand py-2 text-[13px] font-bold text-white">
                <Check className="size-4" /> Approve
              </button>
              <button disabled={busy} onClick={() => onAct({ id: post.id, action: 'reject' })} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-sev-5 py-2 text-[13px] font-bold text-white">
                <X className="size-4" /> Reject
              </button>
            </>
          )}
          {status === 'approved' && (
            <button disabled={busy} onClick={() => onAct({ id: post.id, action: 'hide' })} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-line-2 bg-surface py-2 text-[13px] font-bold">
              <EyeOff className="size-4" /> Hide
            </button>
          )}
          {status === 'hidden' && (
            <button disabled={busy} onClick={() => onAct({ id: post.id, action: 'unhide' })} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-brand py-2 text-[13px] font-bold text-white">
              <Eye className="size-4" /> Unhide
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
