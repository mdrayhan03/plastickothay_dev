import { Award, Layers, ShieldCheck, Sparkles } from 'lucide-react'

const LEVEL_TIERS = [
  { level: 1, title: 'Scout', minPoints: 0 },
  { level: 2, title: 'Reporter', minPoints: 100 },
  { level: 3, title: 'Guardian', minPoints: 300 },
  { level: 4, title: 'Protector', minPoints: 600 },
  { level: 5, title: 'Hero', minPoints: 1000 },
  { level: 6, title: 'Champion', minPoints: 1500 },
  { level: 7, title: 'Legend', minPoints: 2100 },
  { level: 8, title: 'Master', minPoints: 2800 },
  { level: 9, title: 'Eco Titan', minPoints: 3600 },
  { level: 10, title: 'Earth Saviour', minPoints: 4500 },
]

const BADGE_RULES = [
  { id: 'first', name: 'First Report', desc: 'Submitted 1st approved report', requirement: '1 Approved Report', points: 25 },
  { id: 'active', name: 'Active Reporter', desc: 'Submitted 5+ reports', requirement: '5 Approved Reports', points: 50 },
  { id: 'liked', name: 'Well Liked', desc: 'Received 10+ likes on reports', requirement: '10 Likes Received', points: 50 },
  { id: 'dedicated', name: 'Dedicated', desc: 'Submitted 20+ reports', requirement: '20 Approved Reports', points: 100 },
  { id: 'supporter', name: 'Supporter', desc: 'Liked 15+ community reports', requirement: '15 Likes Given', points: 30 },
  { id: 'champion', name: 'Champion', desc: 'Reached Top 3 on Leaderboard', requirement: 'Top 3 Leaderboard', points: 150 },
]

export function RulesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-extrabold">System Rules</h1>
        <p className="text-sm text-ink-3">
          Overview of gamification point rewards, level thresholds, and badge criteria.
        </p>
      </div>

      {/* Level Tiers Table */}
      <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2.5">
          <div className="grid size-9 place-items-center rounded-xl bg-gold-soft text-gold">
            <Layers className="size-5" />
          </div>
          <div>
            <h2 className="font-display text-base font-extrabold">Level Progression Tiers</h2>
            <p className="text-[12px] text-ink-3">Required points for each user progression level.</p>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line bg-surface-2 text-[11.5px] font-bold uppercase tracking-wider text-ink-3">
              <tr>
                <th className="px-4 py-3">Level</th>
                <th className="px-4 py-3">Rank Title</th>
                <th className="px-4 py-3 text-right">Required Points</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {LEVEL_TIERS.map((tier) => (
                <tr key={tier.level} className="hover:bg-surface-2/50">
                  <td className="px-4 py-2.5 font-bold">
                    <span className="rounded-full bg-brand-soft px-2.5 py-0.5 text-xs font-extrabold text-brand-deep">
                      Lvl {tier.level}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-semibold text-ink">{tier.title}</td>
                  <td className="px-4 py-2.5 text-right font-display font-extrabold text-ink-2 tnum">
                    {tier.minPoints.toLocaleString()} pts
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Badge Rules List */}
      <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2.5">
          <div className="grid size-9 place-items-center rounded-xl bg-emerald-500/10 text-emerald-500">
            <Award className="size-5" />
          </div>
          <div>
            <h2 className="font-display text-base font-extrabold">Badge Unlock Requirements</h2>
            <p className="text-[12px] text-ink-3">Conditions required for users to unlock system badges.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {BADGE_RULES.map((badge) => (
            <div key={badge.id} className="flex items-start gap-3 rounded-xl border border-line bg-surface-2/60 p-3.5">
              <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-gold-soft text-gold">
                <Sparkles className="size-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-ink">{badge.name}</span>
                  <span className="rounded-full bg-brand-soft px-2 py-0.5 text-[11px] font-extrabold text-brand-deep">
                    +{badge.points} pts
                  </span>
                </div>
                <p className="mt-0.5 text-[12px] text-ink-3">{badge.desc}</p>
                <div className="mt-2 inline-flex items-center gap-1 text-[11.5px] font-bold text-ink-2">
                  <ShieldCheck className="size-3.5 text-brand" /> {badge.requirement}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
