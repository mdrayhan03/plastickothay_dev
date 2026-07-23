import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, Clock, EyeOff, Trash2 } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import { qk } from '@/lib/queryClient'
import { adminService } from '@/services/adminService'

export function AdminDashboard() {
  const { data: stats } = useQuery({ queryKey: qk.adminStats, queryFn: adminService.stats })

  const tiles = [
    { label: 'Pending', value: stats?.pending ?? 0, icon: Clock, color: 'var(--sev-3)' },
    { label: 'Approved', value: stats?.approved ?? 0, icon: CheckCircle2, color: 'var(--brand)' },
    { label: 'Hidden', value: stats?.hidden ?? 0, icon: EyeOff, color: 'var(--ink-3)' },
    { label: 'Rejected', value: stats?.rejected ?? 0, icon: Trash2, color: 'var(--sev-5)' },
  ]
  const chart = tiles.map((t) => ({ name: t.label, value: t.value, color: t.color }))

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl font-extrabold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {tiles.map((t) => (
          <div key={t.label} className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-bold uppercase tracking-wide text-ink-2">
                {t.label}
              </span>
              <t.icon className="size-4.5" style={{ color: t.color }} />
            </div>
            <div className="mt-2 font-display text-3xl font-extrabold tnum">{t.value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
        <h2 className="mb-4 font-display text-lg font-bold">Reports by status</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--ink-3)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                cursor={{ fill: 'var(--surface-2)' }}
                contentStyle={{
                  background: 'var(--surface)',
                  border: '1px solid var(--line)',
                  borderRadius: 12,
                  fontSize: 13,
                }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {chart.map((c) => (
                  <Cell key={c.name} fill={c.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
