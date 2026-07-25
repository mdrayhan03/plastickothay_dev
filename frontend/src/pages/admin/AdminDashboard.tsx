import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { CheckCircle2, Clock, FileStack, TrendingUp, Users2 } from 'lucide-react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from 'recharts'
import { DensityMap } from '@/components/admin/DensityMap'
import { useLeaderboard } from '@/hooks/useScoring'
import { qk } from '@/lib/queryClient'
import { severityColor, severityLabel } from '@/lib/severity'
import { statusMeta } from '@/lib/status'
import { adminService } from '@/services/adminService'
import type { Severity } from '@/types'

const tooltipStyle = {
  background: 'var(--surface)',
  border: '1px solid var(--line)',
  borderRadius: 12,
  fontSize: 13,
  color: 'var(--ink)',
}

const actionVerb: Record<string, string> = {
  approve: 'approved',
  reject: 'rejected',
  hide: 'hid',
  unhide: 'unhid',
}

function Card({
  title,
  aside,
  children,
}: {
  title: string
  aside?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-[15px] font-bold">{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  )
}

function weekLabel(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function AdminDashboard() {
  const { data: stats } = useQuery({ queryKey: qk.adminStats, queryFn: adminService.stats })
  const { data: markers = [] } = useQuery({ queryKey: qk.adminMap, queryFn: adminService.map })
  const { data: analytics } = useQuery({ queryKey: qk.adminAnalytics, queryFn: adminService.analytics })
  const { data: board } = useLeaderboard('all')
  const { data: audit } = useQuery({ queryKey: qk.adminAudit, queryFn: () => adminService.audit() })

  const kpis = [
    { label: 'Pending review', value: stats?.pending ?? 0, icon: Clock, color: 'var(--gold)' },
    { label: 'Approved', value: stats?.approved ?? 0, icon: CheckCircle2, color: 'var(--brand)' },
    { label: 'Total reports', value: stats?.total ?? 0, icon: FileStack, color: 'var(--ink)' },
    { label: 'Active users', value: analytics?.active_users ?? 0, icon: Users2, color: 'var(--brand-2)' },
  ]

  const statusKey = ['rejected', 'approved', 'pending', 'hidden'] as const
  const statusData = stats
    ? ([2, 1, 3, 0] as const)
        .map((s) => ({ name: statusMeta[s].label, value: stats[statusKey[s]], color: statusMeta[s].dot }))
        .filter((d) => d.value > 0)
    : []

  const severityData = ([1, 2, 3, 4, 5] as Severity[]).map((s) => ({
    name: severityLabel[s],
    value: markers.filter((m) => m.severity === s).length,
    color: severityColor[s],
  }))

  const overTime = (analytics?.over_time ?? []).map((w) => ({ ...w, label: weekLabel(w.week) }))
  const top = board?.results.slice(0, 5) ?? []
  const activity = audit?.results.slice(0, 6) ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-extrabold">Dashboard</h1>
        <p className="text-sm text-ink-3">Where plastic is worst, and what needs your attention.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-[11.5px] font-bold uppercase tracking-wide text-ink-3">{k.label}</span>
              <k.icon className="size-4.5" style={{ color: k.color }} />
            </div>
            <div className="mt-2 font-display text-3xl font-extrabold tnum">{k.value.toLocaleString()}</div>
          </div>
        ))}
      </div>

      <Card
        title="Report density"
        aside={<span className="text-[11.5px] text-ink-3">all reports · every status</span>}
      >
        <div className="h-[380px] overflow-hidden rounded-xl border border-line">
          <DensityMap center={[23.78, 90.4]} zoom={12} markers={markers} />
        </div>
      </Card>

      <Card title="Reports over time" aside={<span className="text-[11.5px] text-ink-3">last 8 weeks</span>}>
        {overTime.length === 0 ? (
          <p className="py-10 text-center text-sm text-ink-3">No activity in this window yet.</p>
        ) : (
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={overTime}>
                <defs>
                  <linearGradient id="submitted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--gold)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--gold)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="approved" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--brand)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--brand)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
                <XAxis dataKey="label" stroke="var(--ink-3)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="submitted" stroke="var(--gold)" strokeWidth={2} fill="url(#submitted)" />
                <Area type="monotone" dataKey="approved" stroke="var(--brand)" strokeWidth={2} fill="url(#approved)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
        <div className="mt-2 flex justify-center gap-5 text-[12px] font-semibold text-ink-2">
          <span className="inline-flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-gold" /> Submitted
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-brand" /> Approved
          </span>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="By status">
          <div className="flex items-center gap-6">
            <div className="h-48 w-48 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusData} dataKey="value" innerRadius={52} outerRadius={78} paddingAngle={2} stroke="none">
                    {statusData.map((d) => (
                      <Cell key={d.name} fill={d.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="flex-1 space-y-2 text-sm">
              {statusData.map((d) => (
                <li key={d.name} className="flex items-center gap-2">
                  <span className="size-2.5 rounded-full" style={{ background: d.color }} />
                  <span className="font-semibold text-ink-2">{d.name}</span>
                  <span className="ml-auto font-bold tnum">{d.value}</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>

        <Card title="By severity">
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityData}>
                <XAxis dataKey="name" stroke="var(--ink-3)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'var(--surface-2)' }} contentStyle={tooltipStyle} />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {severityData.map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Top contributors" aside={<TrendingUp className="size-4 text-gold" />}>
          {top.length === 0 ? (
            <p className="py-6 text-center text-sm text-ink-3">No contributors yet.</p>
          ) : (
            <ol className="space-y-1">
              {top.map((r) => (
                <li key={r.user_id} className="flex items-center gap-3 rounded-xl px-2 py-2 hover:bg-surface-2">
                  <span className="grid size-7 place-items-center rounded-full bg-surface-2 text-[12px] font-extrabold tnum text-ink-2">
                    {r.rank}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-sm font-semibold">{r.full_name || r.username}</span>
                  <span className="font-display text-sm font-extrabold text-gold tnum">{r.points.toLocaleString()}</span>
                </li>
              ))}
            </ol>
          )}
        </Card>

        <Card title="Recent activity">
          {activity.length === 0 ? (
            <div className="grid min-h-40 place-items-center px-6 text-center">
              <p className="text-sm text-ink-3">No moderation actions yet.</p>
            </div>
          ) : (
            <ul className="space-y-2.5">
              {activity.map((e) => (
                <li key={e.id} className="flex items-center gap-2 text-[13px]">
                  <span className="min-w-0 flex-1 truncate text-ink-2">
                    <b className="text-ink">{e.admin}</b> {actionVerb[e.action] ?? e.action} report{' '}
                    <b className="text-ink">#{e.post_id}</b>
                  </span>
                  <time className="shrink-0 text-[11.5px] text-ink-3">
                    {formatDistanceToNow(new Date(e.at), { addSuffix: true })}
                  </time>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  )
}
