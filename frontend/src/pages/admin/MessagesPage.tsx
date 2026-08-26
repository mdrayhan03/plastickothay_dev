import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Mail, Phone, Reply } from 'lucide-react'
import { qk } from '@/lib/queryClient'
import { cn } from '@/lib/utils'
import { adminService } from '@/services/adminService'
import type { ContactMessage } from '@/types'

const statusCls: Record<string, string> = {
  new: 'bg-brand-soft text-brand-deep',
  read: 'bg-surface-2 text-ink-2',
  replied: 'bg-gold-soft text-[#9A6B12]',
}

function mailtoHref(m: ContactMessage) {
  const subject = encodeURIComponent(`Re: ${m.subject}`)
  const body = encodeURIComponent(`\n\n- \nIn reply to your message to PlasticKothay:\n> ${m.message}`)
  return `mailto:${m.email}?subject=${subject}&body=${body}`
}

export function MessagesPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: qk.adminMessages,
    queryFn: () => adminService.messages(),
  })
  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => adminService.setMessageStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.adminMessages }),
  })
  const items = data?.results ?? []

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-extrabold">Contact messages</h1>
        <p className="text-sm text-ink-3">Reply opens your email client - the app doesn’t send mail itself.</p>
      </div>

      {isLoading && <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />}
      {!isLoading && items.length === 0 && (
        <p className="rounded-2xl border border-line bg-surface p-10 text-center text-sm text-ink-3">No messages.</p>
      )}

      <div className="space-y-3">
        {items.map((m) => (
          <div key={m.id} className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="font-bold">{m.subject}</div>
                <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-ink-2">
                  <span className="font-semibold text-ink">{m.name}</span>
                  <a href={`mailto:${m.email}`} className="inline-flex items-center gap-1 hover:text-brand">
                    <Mail className="size-3.5" /> {m.email}
                  </a>
                  {m.phone && (
                    <span className="inline-flex items-center gap-1">
                      <Phone className="size-3.5" /> {m.phone}
                    </span>
                  )}
                </div>
              </div>
              <span
                className={cn(
                  'shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold uppercase',
                  statusCls[m.status] ?? statusCls.new,
                )}
              >
                {m.status}
              </span>
            </div>

            <p className="mt-2.5 text-sm text-ink-2">{m.message}</p>

            <div className="mt-3 flex flex-wrap gap-2">
              <a
                href={mailtoHref(m)}
                onClick={() => setStatus.mutate({ id: m.id, status: 'replied' })}
                className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-3.5 py-1.5 text-[12.5px] font-bold text-white"
              >
                <Reply className="size-4" /> Reply by email
              </a>
              {['read', 'replied'].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatus.mutate({ id: m.id, status: s })}
                  className="rounded-lg border border-line-2 bg-surface px-3.5 py-1.5 text-[12.5px] font-bold capitalize text-ink-2 hover:bg-surface-2"
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
