import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, ArrowUpDown, Award, BadgeCheck, Camera, Crown, Handshake, Heart, Mail, Phone, Sprout, Trash2, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { RoleChip, SeverityChip, StatusChip } from '@/components/admin/Chips'
import { Drawer } from '@/components/admin/Drawer'
import { ReportDrawer } from '@/components/admin/ReportDrawer'
import { useAuth } from '@/context/auth-context'
import { apiErrorMessage } from '@/lib/api'
import { canChangeRole, canDeleteUser } from '@/lib/permissions'
import { qk } from '@/lib/queryClient'
import { cn } from '@/lib/utils'
import { adminService } from '@/services/adminService'
import type { AdminPost, AdminUser, Role } from '@/types'

const ROLE_TABS = [
  { key: 'all', label: 'All' },
  { key: 'admin', label: 'Admins' },
  { key: 'staff', label: 'Staff' },
  { key: 'user', label: 'Users' },
] as const

const BADGES = [
  { id: 'first', name: 'First Report', icon: Sprout, check: (_u: AdminUser, d: any) => (d?.posts_approved ?? 0) >= 1 },
  { id: 'active', name: 'Active Reporter', icon: Camera, check: (_u: AdminUser, d: any) => (d?.posts_approved ?? 0) >= 5 },
  { id: 'liked', name: 'Well Liked', icon: Heart, check: (_u: AdminUser, d: any) => (d?.likes_received ?? 0) >= 10 },
  { id: 'dedicated', name: 'Dedicated', icon: Award, check: (_u: AdminUser, d: any) => (d?.posts_approved ?? 0) >= 20 },
  { id: 'supporter', name: 'Supporter', icon: Handshake, check: (_u: AdminUser, _d: any) => true },
  { id: 'champion', name: 'Champion', icon: Crown, check: (_u: AdminUser, d: any) => (d?.total_points ?? 0) >= 1000 },
]

export function UsersPage() {
  const qc = useQueryClient()
  const { user: me } = useAuth()
  const isAdmin = me?.role === 'admin'
  const [roleTab, setRoleTab] = useState<(typeof ROLE_TABS)[number]['key']>('all')
  const [activeOnly, setActiveOnly] = useState<'all' | 'active' | 'inactive'>('all')
  const [openId, setOpenId] = useState<number | null>(null)
  const [selectedReport, setSelectedReport] = useState<AdminPost | null>(null)
  const [params, setParams] = useSearchParams()
  const q = params.get('q')?.trim().toLowerCase() ?? ''

  const { data, isLoading, isError, error } = useQuery({
    queryKey: qk.adminUsers,
    queryFn: () => adminService.users(),
    retry: false,
  })

  const setActive = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) => adminService.setActive(id, active),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.adminUsers })
      toast.success('Updated')
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  })

  const users = (data?.results ?? [])
    .filter((u) => (roleTab === 'all' ? true : u.role === roleTab))
    .filter((u) => (activeOnly === 'all' ? true : activeOnly === 'active' ? u.is_active : !u.is_active))
    .filter((u) =>
      q ? `${u.first_name} ${u.last_name} ${u.username} ${u.email}`.toLowerCase().includes(q) : true,
    )

  const open = data?.results.find((u) => u.id === openId) ?? null

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-extrabold">Users</h1>

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

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-xl border border-line bg-surface-2 p-1">
          {ROLE_TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setRoleTab(t.key)}
              className={cn(
                'rounded-lg px-3.5 py-2 text-[13px] font-bold transition-colors',
                roleTab === t.key ? 'bg-surface text-ink shadow-sm' : 'text-ink-2',
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
        <select
          value={activeOnly}
          onChange={(e) => setActiveOnly(e.target.value as typeof activeOnly)}
          className="rounded-xl border border-line bg-surface px-3 py-2.5 text-[13px] font-semibold"
        >
          <option value="all">All accounts</option>
          <option value="active">Active only</option>
          <option value="inactive">Inactive only</option>
        </select>
      </div>

      {isLoading && <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />}

      {isError && <PendingNotice error={apiErrorMessage(error)} />}

      {!isLoading && !isError && (
        <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-sm">
          {users.length === 0 && (
            <p className="p-10 text-center text-sm text-ink-3">No users match this filter.</p>
          )}
          {users.map((u) => (
            <button
              key={u.id}
              onClick={() => setOpenId(u.id)}
              className="flex w-full items-center gap-3 border-b border-line px-4 py-3 text-left last:border-b-0 hover:bg-surface-2/60"
            >
              <Avatar user={u} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5 truncate text-sm font-bold">
                  {u.first_name} {u.last_name}
                  {u.is_verified && <BadgeCheck className="size-3.5 text-brand" />}
                </div>
                <div className="truncate text-[12.5px] text-ink-3">{u.email}</div>
              </div>
              {!u.is_active && (
                <span className="rounded-full bg-surface-2 px-2 py-0.5 text-[10.5px] font-bold uppercase text-ink-3">
                  Inactive
                </span>
              )}
              <RoleChip role={u.role} />
            </button>
          ))}
        </div>
      )}

      <UserDrawer
        user={open}
        isAdmin={isAdmin}
        isSelf={open?.id === me?.id}
        onClose={() => setOpenId(null)}
        onToggleActive={(u) => setActive.mutate({ id: u.id, active: !u.is_active })}
        onSelectReport={(r) => setSelectedReport(r)}
        busy={setActive.isPending}
      />

      <ReportDrawer
        post={selectedReport}
        onClose={() => setSelectedReport(null)}
        onAct={() => setSelectedReport(null)}
        busy={false}
      />
    </div>
  )
}

function Avatar({ user }: { user: AdminUser }) {
  return (
    <div className="grid size-9 shrink-0 place-items-center rounded-full bg-[linear-gradient(135deg,var(--brand-2),var(--brand-deep))] text-[13px] font-extrabold text-white">
      {(user.first_name[0] ?? user.username[0] ?? '?').toUpperCase()}
    </div>
  )
}

function PendingNotice({ error }: { error: string }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-gold/40 bg-gold-soft/50 p-5">
      <AlertTriangle className="mt-0.5 size-5 shrink-0 text-gold" />
      <div className="text-sm">
        <div className="font-bold text-ink">The admin users API isn’t live yet.</div>
        <p className="mt-1 text-ink-2">
          This screen is built and ready; it needs the <b>Users list / activate / role</b> endpoints
          (BE-0 in the backend TODO). Until then: <span className="text-ink-3">{error}</span>
        </p>
      </div>
    </div>
  )
}

function UserDrawer({
  user,
  isAdmin,
  isSelf,
  onClose,
  onToggleActive,
  onSelectReport,
  busy,
}: {
  user: AdminUser | null
  isAdmin: boolean
  isSelf: boolean
  onClose: () => void
  onToggleActive: (u: AdminUser) => void
  onSelectReport: (r: AdminPost) => void
  busy: boolean
}) {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<'all' | number>('all')
  const [sortOrder, setSortOrder] = useState<'latest' | 'oldest'>('latest')

  const { data: detail } = useQuery({
    queryKey: user ? qk.adminUserDetail(user.id) : ['admin', 'users', 'none'],
    queryFn: () => adminService.userDetail(user!.id),
    enabled: !!user,
    retry: false,
  })

  // Fetch reports submitted by this user
  const { data: reportsData } = useQuery({
    queryKey: user ? ['admin', 'user-reports', user.id] : ['admin', 'user-reports', 'none'],
    queryFn: () => adminService.reports({ user_id: user!.id }),
    enabled: !!user,
  })

  // Memoise off the stable query data so the downstream useMemos don't recompute every render.
  const userReports = useMemo(() => reportsData?.results ?? [], [reportsData])

  // Status counts for filter pills
  const counts = useMemo(
    () => ({
      all: userReports.length,
      approved: userReports.filter((p) => p.status === 1).length,
      pending: userReports.filter((p) => p.status === 2).length,
      rejected: userReports.filter((p) => p.status === 0).length,
    }),
    [userReports],
  )

  // Filtered & sorted timeline posts
  const filteredReports = useMemo(() => {
    let result = [...userReports]
    if (statusFilter !== 'all') {
      result = result.filter((p) => p.status === statusFilter)
    }
    result.sort((a, b) => {
      const timeA = new Date(a.created).getTime()
      const timeB = new Date(b.created).getTime()
      return sortOrder === 'latest' ? timeB - timeA : timeA - timeB
    })
    return result
  }, [userReports, statusFilter, sortOrder])

  const setRole = useMutation({
    mutationFn: ({ id, role }: { id: number; role: Role }) => adminService.setRole(id, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.adminUsers })
      toast.success('Role updated')
    },
    onError: () => toast.error('Changing roles needs the admin API (BE-0).'),
  })
  const del = useMutation({
    mutationFn: (id: number) => adminService.deleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.adminUsers })
      onClose()
      toast.success('User deleted')
    },
    onError: () => toast.error('Deleting users needs the admin API (BE-2).'),
  })

  const stat = (v?: number) => (v == null ? '-' : v.toLocaleString())
  const roleEditable = user ? canChangeRole(isAdmin, isSelf) : false
  const deletable = user ? canDeleteUser(isAdmin, user, isSelf) : false

  return (
    <Drawer open={!!user} onClose={onClose} title={user ? 'User profile' : ''}>
      {user && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="grid size-14 place-items-center rounded-full bg-[linear-gradient(135deg,var(--brand-2),var(--brand-deep))] text-xl font-extrabold text-white">
              {(user.first_name[0] ?? user.username[0] ?? '?').toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-1.5 font-display text-lg font-extrabold">
                {user.first_name} {user.last_name}
                {user.is_verified && <BadgeCheck className="size-4 text-brand" />}
              </div>
              <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
                <RoleChip role={user.role} />
                <span className="rounded-full bg-brand-soft px-2.5 py-0.5 text-[11px] font-extrabold text-brand-deep">
                  Lvl {detail?.level ?? 1} {detail?.level_title ? `· ${detail.level_title}` : ''}
                </span>
                {!user.is_active && (
                  <span className="rounded-full bg-surface-2 px-2 py-0.5 text-[10.5px] font-bold uppercase text-ink-3">
                    Inactive
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-2 rounded-2xl border border-line bg-surface-2 p-4 text-[13px]">
            <div className="flex items-center gap-2.5 text-ink-2">
              <Mail className="size-4 text-ink-3" />
              <a href={`mailto:${user.email}`} className="hover:text-brand">
                {user.email}
              </a>
            </div>
            {user.phone && (
              <div className="flex items-center gap-2.5 text-ink-2">
                <Phone className="size-4 text-ink-3" />
                {user.phone}
              </div>
            )}
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-4 gap-2">
            {[
              { label: 'Level', value: detail?.level ? `Lvl ${detail.level}` : 'Lvl 1' },
              { label: 'Reports', value: stat(detail?.posts_approved) },
              { label: 'Likes', value: stat(detail?.likes_received) },
              { label: 'Points', value: stat(detail?.total_points) },
            ].map((s) => (
              <div key={s.label} className="rounded-xl border border-line bg-surface p-2.5 text-center">
                <div className="font-display text-base font-extrabold tnum">{s.value}</div>
                <div className="text-[10px] font-semibold uppercase tracking-wide text-ink-3">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Badges Grid */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wide text-ink-3">Badges</span>
              <span className="text-[11px] font-bold text-ink-3">
                {BADGES.filter((b) => b.check(user, detail)).length} of {BADGES.length}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {BADGES.map((b) => {
                const unlocked = b.check(user, detail)
                const Icon = b.icon
                return (
                  <div
                    key={b.id}
                    className={cn(
                      'flex flex-col items-center gap-1.5 rounded-xl border p-2.5 text-center transition-all',
                      unlocked
                        ? 'border-gold/40 bg-gold-soft/30 text-ink'
                        : 'border-line bg-surface-2/40 opacity-40 grayscale',
                    )}
                  >
                    <div className={cn('grid size-8 place-items-center rounded-lg', unlocked ? 'bg-gold/20 text-gold' : 'bg-surface-2 text-ink-3')}>
                      <Icon className="size-4.5" />
                    </div>
                    <span className="text-[11px] font-bold leading-tight">{b.name}</span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Role Controls */}
          <div>
            <div className="mb-2 text-[11px] font-extrabold uppercase tracking-wide text-ink-3">Role</div>
            <div className="flex gap-2">
              {(['user', 'staff', 'admin'] as Role[]).map((r) => (
                <button
                  key={r}
                  disabled={!roleEditable || setRole.isPending}
                  onClick={() => setRole.mutate({ id: user.id, role: r })}
                  className={cn(
                    'flex-1 rounded-xl border py-2 text-[13px] font-bold capitalize transition-colors',
                    user.role === r ? 'border-brand bg-brand-soft text-brand-deep' : 'border-line-2 text-ink-2',
                    !roleEditable && 'cursor-not-allowed opacity-50',
                  )}
                >
                  {r}
                </button>
              ))}
            </div>
            {!isAdmin && <p className="mt-2 text-[11.5px] text-ink-3">Only admins can change roles.</p>}
            {isAdmin && isSelf && <p className="mt-2 text-[11.5px] text-ink-3">You can’t change your own role.</p>}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2 border-b border-line pb-5">
            <button
              disabled={busy || isSelf}
              onClick={() => onToggleActive(user)}
              className={cn(
                'flex-1 rounded-xl border py-2.5 text-[13px] font-bold disabled:opacity-50',
                user.is_active ? 'border-line-2 text-ink-2' : 'border-brand bg-brand-soft text-brand-deep',
              )}
            >
              {user.is_active ? 'Deactivate' : 'Activate'}
            </button>
            {deletable && (
              <button
                disabled={del.isPending}
                onClick={() => del.mutate(user.id)}
                className="flex items-center justify-center gap-1.5 rounded-xl border border-sev-5/40 px-4 py-2.5 text-[13px] font-bold text-sev-5 hover:bg-sev-5/10 disabled:opacity-50"
              >
                <Trash2 className="size-4" /> Delete
              </button>
            )}
          </div>

          {/* Reports Timeline at Bottom */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-extrabold uppercase tracking-wide text-ink-3">Reports Timeline</span>
                <p className="text-[11.5px] font-semibold text-ink-3">{userReports.length} total reports</p>
              </div>

              <button
                type="button"
                onClick={() => setSortOrder((prev) => (prev === 'latest' ? 'oldest' : 'latest'))}
                className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-[11.5px] font-bold text-ink shadow-sm transition hover:bg-surface-2"
              >
                <ArrowUpDown className="size-3 text-brand" />
                <span>{sortOrder === 'latest' ? 'Latest' : 'Oldest'}</span>
              </button>
            </div>

            {/* Status Filter Pills */}
            <div className="mb-3 flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {[
                { id: 'all', label: 'All', count: counts.all },
                { id: 1, label: 'Approved', count: counts.approved },
                { id: 2, label: 'Pending', count: counts.pending },
                { id: 0, label: 'Rejected', count: counts.rejected },
              ].map((item) => {
                const isActive = statusFilter === item.id
                return (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() => setStatusFilter(item.id as 'all' | number)}
                    className={`flex flex-none items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold transition ${
                      isActive
                        ? 'bg-brand text-white shadow-sm'
                        : 'border border-line bg-surface text-ink-2 hover:bg-surface-2'
                    }`}
                  >
                    <span>{item.label}</span>
                    <span
                      className={`rounded-full px-1.5 py-0.5 text-[10px] font-extrabold ${
                        isActive ? 'bg-white/20 text-white' : 'bg-surface-2 text-ink-3'
                      }`}
                    >
                      {item.count}
                    </span>
                  </button>
                )
              })}
            </div>

            {/* Reports List */}
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1 scrollbar-none">
              {filteredReports.length === 0 ? (
                <p className="rounded-xl border border-line bg-surface-2/50 p-4 text-center text-xs text-ink-3">
                  No reports match this filter.
                </p>
              ) : (
                filteredReports.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => onSelectReport(r)}
                    className="flex w-full items-center gap-3 rounded-xl border border-line bg-surface p-2.5 text-left transition-colors hover:border-brand/40"
                  >
                    <img src={r.image_url} alt="" className="size-10 rounded-lg object-cover bg-surface-2 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[12.5px] font-bold text-ink">
                        {r.place_name || 'Pollution Report'}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[11px] text-ink-3">
                        <StatusChip status={r.status} />
                        <SeverityChip severity={r.severity} />
                        <span className="ml-auto inline-flex items-center gap-1 font-semibold">
                          <Heart className="size-3 text-heart fill-heart/20" /> {r.likes ?? 0}
                        </span>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </Drawer>
  )
}

