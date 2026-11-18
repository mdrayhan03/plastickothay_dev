import { useQuery } from '@tanstack/react-query'
import { Award, Trophy, User as UserIcon } from 'lucide-react'
import { useState } from 'react'
import { qk } from '@/lib/queryClient'
import { cn } from '@/lib/utils'
import { scoringService } from '@/services/scoringService'
import type { LeaderboardRow } from '@/types'

const TIMEFRAMES = [
  { key: 'all', label: 'All-Time' },
  { key: 'month', label: 'This Month' },
  { key: 'week', label: 'This Week' },
] as const

export function ContributorsPage() {
  const [timeframe, setTimeframe] = useState<'all' | 'month' | 'week'>('all')

  const { data: leaderboard, isLoading } = useQuery({
    queryKey: qk.leaderboard(timeframe),
    queryFn: () => scoringService.leaderboard(timeframe),
  })

  const contributors: LeaderboardRow[] = leaderboard?.results ?? []
  const totalPoints = contributors.reduce((acc: number, c: LeaderboardRow) => acc + (c.points || 0), 0)
  const topContributor = contributors[0]

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-extrabold">Top Contributors</h1>
          <p className="text-sm text-ink-3">
            Leaderboard ranking of reporters, points earned, and community impact.
          </p>
        </div>
        
        {/* Timeframe selector */}
        <div className="flex gap-1 rounded-xl border border-line bg-surface-2 p-1">
          {TIMEFRAMES.map((t) => (
            <button
              key={t.key}
              onClick={() => setTimeframe(t.key)}
              className={cn(
                'rounded-lg px-3.5 py-1.5 text-[13px] font-bold transition-colors',
                timeframe === t.key ? 'bg-surface text-ink shadow-sm' : 'text-ink-2',
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-line bg-surface p-4.5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center rounded-xl bg-brand-soft text-brand-deep">
              <Trophy className="size-5" />
            </div>
            <div>
              <div className="font-display text-2xl font-extrabold tnum">{contributors.length}</div>
              <div className="text-[12px] font-bold text-ink-3">Active Contributors</div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-line bg-surface p-4.5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center rounded-xl bg-gold-soft text-gold">
              <Award className="size-5" />
            </div>
            <div>
              <div className="font-display text-2xl font-extrabold tnum">{totalPoints.toLocaleString()}</div>
              <div className="text-[12px] font-bold text-ink-3">Total Points Awarded</div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-line bg-surface p-4.5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center rounded-xl bg-emerald-500/10 text-emerald-500">
              <UserIcon className="size-5" />
            </div>
            <div className="min-w-0">
              <div className="truncate font-display text-base font-extrabold">
                {topContributor ? (topContributor.full_name || topContributor.username) : '—'}
              </div>
              <div className="text-[12px] font-bold text-ink-3">#1 Leaderboard Contributor</div>
            </div>
          </div>
        </div>
      </div>

      {/* Leaderboard Ranking Table */}
      {isLoading ? (
        <div className="h-60 animate-pulse rounded-2xl bg-surface-2" />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line bg-surface-2 text-[11.5px] font-bold uppercase tracking-wider text-ink-3">
                <tr>
                  <th className="px-4 py-3.5">Rank</th>
                  <th className="px-4 py-3.5">Contributor</th>
                  <th className="px-4 py-3.5 text-right">Points Earned</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {contributors.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="p-8 text-center text-ink-3">
                      No contributor activity for this timeframe.
                    </td>
                  </tr>
                ) : (
                  contributors.map((item: LeaderboardRow, idx: number) => {
                    const rank = item.rank || (idx + 1)
                    const name = item.full_name || item.username
                    return (
                      <tr key={item.user_id} className="transition-colors hover:bg-surface-2/60">
                        {/* Rank */}
                        <td className="px-4 py-3.5 font-bold">
                          <div className="flex items-center gap-2">
                            {rank === 1 && (
                              <span className="grid size-7 place-items-center rounded-full bg-gold/20 text-gold font-extrabold text-xs">
                                🥇 1
                              </span>
                            )}
                            {rank === 2 && (
                              <span className="grid size-7 place-items-center rounded-full bg-slate-400/20 text-slate-400 font-extrabold text-xs">
                                🥈 2
                              </span>
                            )}
                            {rank === 3 && (
                              <span className="grid size-7 place-items-center rounded-full bg-amber-700/20 text-amber-600 font-extrabold text-xs">
                                🥉 3
                              </span>
                            )}
                            {rank > 3 && <span className="text-ink-3 pl-2">#{rank}</span>}
                          </div>
                        </td>

                        {/* User */}
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-3">
                            <div className="grid size-9 place-items-center rounded-full bg-[linear-gradient(135deg,var(--brand-2),var(--brand-deep))] text-xs font-extrabold text-white">
                              {(name[0] ?? '?').toUpperCase()}
                            </div>
                            <div>
                              <div className="font-bold text-ink">{name}</div>
                              <div className="text-[11.5px] text-ink-3">@{item.username}</div>
                            </div>
                          </div>
                        </td>

                        {/* Points */}
                        <td className="px-4 py-3.5 text-right font-display text-base font-extrabold text-brand tnum">
                          {item.points.toLocaleString()} pts
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
