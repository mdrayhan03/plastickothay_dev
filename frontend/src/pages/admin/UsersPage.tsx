import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiErrorMessage } from '@/lib/api'
import { adminService } from '@/services/adminService'
import { cn } from '@/lib/utils'

const roleCls: Record<string, string> = {
  admin: 'bg-[#2b2140] text-[#b79cf0]',
  staff: 'bg-brand-soft text-brand-deep',
  user: 'bg-surface-2 text-ink-2',
}

export function UsersPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['admin', 'users'], queryFn: () => adminService.users() })
  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) => adminService.setActive(id, active),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      toast.success('Updated')
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  })
  const users = data?.results ?? []

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-extrabold">Users</h1>
      {isLoading && <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />}
      <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-sm">
        {users.map((u) => (
          <div key={u.id} className="flex items-center gap-3 border-b border-line px-4 py-3 last:border-b-0">
            <div className="grid size-9 place-items-center rounded-full bg-[linear-gradient(135deg,var(--brand-2),var(--brand-deep))] text-[13px] font-extrabold text-white">
              {u.first_name[0]?.toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-bold">
                {u.first_name} {u.last_name}
              </div>
              <div className="truncate text-[12.5px] text-ink-3">{u.email}</div>
            </div>
            <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-bold uppercase', roleCls[u.role])}>
              {u.role}
            </span>
            {u.role !== 'admin' && (
              <button
                onClick={() => toggle.mutate({ id: u.id, active: !u.is_active })}
                className={cn(
                  'rounded-lg border px-3 py-1.5 text-[12.5px] font-bold',
                  u.is_active ? 'border-line-2 text-ink-2' : 'border-brand bg-brand-soft text-brand-deep',
                )}
              >
                {u.is_active ? 'Deactivate' : 'Activate'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
