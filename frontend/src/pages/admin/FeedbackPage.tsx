import { useQuery } from '@tanstack/react-query'
import { Star } from 'lucide-react'
import { qk } from '@/lib/queryClient'
import { adminService } from '@/services/adminService'

export function FeedbackPage() {
  const { data, isLoading } = useQuery({
    queryKey: qk.adminFeedback,
    queryFn: () => adminService.feedback(),
  })
  const items = data?.results ?? []

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-extrabold">Feedback</h1>
      {isLoading && <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />}
      {!isLoading && items.length === 0 && (
        <p className="rounded-2xl border border-line bg-surface p-10 text-center text-sm text-ink-3">
          No feedback yet.
        </p>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((f) => (
          <div key={f.id} className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }, (_, i) => (
                <Star
                  key={i}
                  className="size-4"
                  fill={i < f.rating ? 'var(--gold)' : 'none'}
                  stroke={i < f.rating ? 'var(--gold)' : 'var(--line-2)'}
                />
              ))}
            </div>
            {f.comment && <p className="mt-2 text-sm text-ink-2">{f.comment}</p>}
            <div className="mt-2 text-[12px] font-semibold text-ink-3">{f.name || 'Anonymous'}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
