import { useState } from 'react'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { useLeaderboard } from '@/hooks/useScoring'
import { cn } from '@/lib/utils'
import type { LeaderboardRow } from '@/types'

const PERIODS = [
  { key: 'week', label: 'Week' },
  { key: 'month', label: 'Month' },
  { key: 'year', label: 'Year' },
  { key: 'all', label: 'All' },
] as const

function initials(name: string) {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function Podium({ rows }: { rows: LeaderboardRow[] }) {
  const [first, second, third] = [rows[0], rows[1], rows[2]]
  const cell = (row: LeaderboardRow | undefined, place: 1 | 2 | 3) => {
    if (!row) return <div />
    const big = place === 1
    const barH = place === 1 ? 'h-16' : place === 2 ? 'h-11' : 'h-8'
    return (
      <div className="flex flex-col items-center gap-2 text-center">
        <div
          className={cn(
            'relative grid place-items-center rounded-full font-extrabold text-white',
            big ? 'size-17 text-[22px] ring-3 ring-gold' : 'size-14 text-[19px]',
          )}
          style={{ background: 'linear-gradient(135deg,var(--brand-2),var(--brand-deep))' }}
        >
          {big && <span className="absolute -top-4 text-lg">👑</span>}
          {initials(row.full_name || row.username)}
        </div>
        <div className="text-[12.5px] font-bold leading-tight">{row.username}</div>
        <div className="font-display text-[15px] font-bold text-gold tnum">{row.points}</div>
        <div
          className={cn(
            'grid w-full place-items-start justify-center rounded-t-xl pt-2 font-extrabold text-brand-deep',
            barH,
          )}
          style={{ background: 'linear-gradient(var(--brand-soft),transparent)' }}
        >
          {place}
        </div>
      </div>
    )
  }
  return (
    <div className="grid grid-cols-3 items-end gap-2.5 px-5.5 pb-1.5 pt-6">
      {cell(second, 2)}
      {cell(first, 1)}
      {cell(third, 3)}
    </div>
  )
}

export function LeaderboardPage() {
  const [period, setPeriod] = useState<(typeof PERIODS)[number]['key']>('week')
  const { user } = useAuth()
  const { data, isLoading } = useLeaderboard(period)
  const rows = data?.results ?? []
  const rest = rows.slice(3)
  const you = rows.find((r) => r.user_id === user?.id)

  return (
    <>
      <TopBar title="Leaderboard" />

      <div className="mx-4.5 mt-3.5 flex gap-1 rounded-2xl border border-line bg-surface-2 p-1">
        {PERIODS.map((p) => (
          <button
            key={p.key}
            onClick={() => setPeriod(p.key)}
            className={cn(
              'h-9.5 flex-1 rounded-[10px] text-[13px] font-bold transition-colors',
              period === p.key ? 'bg-surface text-ink shadow-sm' : 'text-ink-2',
            )}
          >
            {p.label}
          </button>
        ))}
      </div>

      {isLoading && <div className="mx-4.5 mt-8 h-40 animate-pulse rounded-2xl bg-surface-2" />}

      {!isLoading && rows.length > 0 && <Podium rows={rows} />}

      {you && (
        <div className="mx-3 my-1.5 flex items-center gap-3 rounded-2xl bg-brand-soft p-3">
          <div className="w-6 text-center font-display text-[15px] font-bold text-brand-deep tnum">
            {you.rank}
          </div>
          <div className="grid size-9.5 place-items-center rounded-full bg-[linear-gradient(135deg,var(--brand-2),var(--brand-deep))] text-sm font-extrabold text-white">
            {initials(you.full_name || you.username)}
          </div>
          <div className="flex-1 text-[14.5px] font-semibold">
            You
            <small className="block text-[11.5px] font-semibold text-brand-deep/70">
              {you.full_name}
            </small>
          </div>
          <div className="font-display text-base font-bold text-brand-deep tnum">{you.points}</div>
        </div>
      )}

      {rest.map((row) => (
        <div key={row.user_id} className="flex items-center gap-3 border-b border-line px-4.5 py-3">
          <div className="w-6 text-center font-display text-[15px] font-bold text-ink-3 tnum">
            {row.rank}
          </div>
          <div className="grid size-9.5 place-items-center rounded-full bg-[linear-gradient(135deg,var(--brand-2),var(--brand-deep))] text-[13px] font-extrabold text-white">
            {initials(row.full_name || row.username)}
          </div>
          <div className="flex-1 text-[14.5px] font-semibold">
            {row.full_name || row.username}
            <small className="block text-[11.5px] font-semibold text-ink-3">@{row.username}</small>
          </div>
          <div className="font-display text-base font-bold tnum">{row.points}</div>
        </div>
      ))}

      {!isLoading && rows.length === 0 && (
        <p className="px-8 py-12 text-center text-sm text-ink-3">
          No points yet this period. Get reporting!
        </p>
      )}
    </>
  )
}
