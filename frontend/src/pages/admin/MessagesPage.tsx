import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/adminService'
import { cn } from '@/lib/utils'

const statusCls: Record<string, string> = {
  new: 'bg-brand-soft text-brand-deep',
  read: 'bg-surface-2 text-ink-2',
  replied: 'bg-gold-soft text-[#9A6B12]',
}

export function MessagesPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'messages'],
    queryFn: () => adminService.messages(),
  })
  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      adminService.setMessageStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'messages'] }),
  })
  const items = data?.results ?? []

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-extrabold">Contact messages</h1>
      {isLoading && <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />}
      {!isLoading && items.length === 0 && (
        <p className="rounded-2xl border border-line bg-surface p-10 text-center text-sm text-ink-3">
          No messages.
        </p>
      )}
      <div className="space-y-3">
        {items.map((m) => (
          <div key={m.id} className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-bold">{m.subject}</div>
                <div className="text-[13px] text-ink-2">
                  {m.name} · {m.email}
                  {m.phone && ` · ${m.phone}`}
                </div>
              </div>
              <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-bold uppercase', statusCls[m.status] ?? statusCls.new)}>
                {m.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-ink-2">{m.message}</p>
            <div className="mt-3 flex gap-2">
              {['read', 'replied'].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatus.mutate({ id: m.id, status: s })}
                  className="rounded-lg border border-line-2 bg-surface px-3 py-1.5 text-[12.5px] font-bold capitalize"
                >
                  Mark {s}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
