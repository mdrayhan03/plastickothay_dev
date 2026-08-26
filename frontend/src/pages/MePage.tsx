import { Moon, Pencil } from 'lucide-react'
import { Link } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { useOwnPosts } from '@/hooks/usePosts'
import { useBadges, useContribution } from '@/hooks/useScoring'
import { useTheme } from '@/hooks/useTheme'
import { severityLabel } from '@/lib/severity'
import type { PostStatus } from '@/types'

const statusChip: Record<PostStatus, { label: string; cls: string }> = {
  1: { label: 'Approved', cls: 'bg-brand-soft text-brand-deep' },
  2: { label: 'Pending', cls: 'bg-[#FBEFD6] text-[#9A6B12] dark:bg-[#3a2f14] dark:text-[#e6b84e]' },
  3: { label: 'Hidden', cls: 'bg-surface-2 text-ink-3' },
  0: { label: 'Rejected', cls: 'bg-surface-2 text-ink-3' },
}

function Ring({ pct, level, title }: { pct: number; level: number; title: string }) {
  const r = 52
  const circ = 2 * Math.PI * r
  const offset = circ - (Math.min(100, Math.max(0, pct)) / 100) * circ
  return (
    <div className="relative mx-auto grid size-33 place-items-center">
      <svg viewBox="0 0 120 120" className="absolute inset-0 -rotate-90">
        <defs>
          <linearGradient id="lvl" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="var(--brand-2)" />
            <stop offset="1" stopColor="var(--gold)" />
          </linearGradient>
        </defs>
        <circle cx="60" cy="60" r={r} fill="none" stroke="var(--line-2)" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="url(#lvl)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="text-center">
        <b className="block font-display text-3xl leading-none tnum">{level}</b>
        <span className="text-[10.5px] font-extrabold uppercase tracking-wider text-brand">
          {title}
        </span>
      </div>
    </div>
  )
}

export function MePage() {
  const { user } = useAuth()
  const { toggle } = useTheme()
  const { data: c } = useContribution()
  const { data: badges } = useBadges()
  const own = useOwnPosts()
  const posts = own.data?.pages.flatMap((p) => p.results) ?? []
  const earned = new Set(badges?.map((b) => b.code))

  // A small fixed badge catalogue for the "locked" placeholders (icons match the seed).
  const catalogue = [
    { code: 'first_report', icon: '🌱', name: 'First Report' },
    { code: 'reporter_10', icon: '📸', name: 'Active Reporter' },
    { code: 'well_liked', icon: '❤️', name: 'Well Liked' },
    { code: 'reporter_50', icon: '🏅', name: 'Dedicated' },
    { code: 'supporter', icon: '🤝', name: 'Supporter' },
    { code: 'champion', icon: '👑', name: 'Champion' },
  ]

  return (
    <>
      <TopBar
        title="My impact"
        right={
          <div className="flex gap-2">
            <Link
              to="/me/edit"
              aria-label="Edit profile"
              className="grid size-10 place-items-center rounded-[13px] bg-surface text-ink shadow-sm"
            >
              <Pencil className="size-[18px]" />
            </Link>
            <button
              type="button"
              onClick={toggle}
              aria-label="Toggle theme"
              className="grid size-10 place-items-center rounded-[13px] bg-surface text-ink shadow-sm"
            >
              <Moon className="size-5" />
            </button>
          </div>
        }
      />

      <div className="px-4.5 pb-1 pt-5 text-center">
        <Ring
          pct={c?.progress_percentage ?? 0}
          level={c?.level ?? 1}
          title={c?.level_title ?? 'Newcomer'}
        />
        <div className="mt-3 font-display text-[22px] font-bold">
          {user ? `${user.first_name} ${user.last_name}` : 'You'}
        </div>
        <div className="mt-0.5 text-[12.5px] font-semibold text-ink-2">
          {c?.total_points ?? 0} pts
          {c?.points_to_next_level != null && (
            <> · {c.points_to_next_level} to next level</>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2.5 px-4.5 pb-1 pt-4">
        {[
          { n: c?.posts_approved ?? 0, l: 'Reports' },
          { n: c?.likes_received ?? 0, l: 'Likes' },
          { n: c?.total_points ?? 0, l: 'Points', reward: true },
        ].map((s) => (
          <div key={s.l} className="rounded-[16px] border border-line bg-surface p-3.5 text-center shadow-sm">
            <b className={`block font-display text-[22px] leading-none tnum ${s.reward ? 'text-gold' : ''}`}>
              {s.n}
            </b>
            <span className="mt-1 block text-[10.5px] font-bold uppercase tracking-wide text-ink-2">
              {s.l}
            </span>
          </div>
        ))}
      </div>

      <div className="mx-4.5 mb-3 mt-5.5 flex items-center justify-between">
        <h2 className="font-display text-lg font-bold">Badges</h2>
        <span className="text-[13px] font-semibold text-ink-2">
          {earned.size} of {catalogue.length}
        </span>
      </div>
      <div className="grid grid-cols-4 gap-3 px-4.5">
        {catalogue.map((b) => {
          const has = earned.has(b.code)
          return (
            <div key={b.code} className="text-center">
              <div
                className={`grid aspect-square place-items-center rounded-[18px] border text-[26px] shadow-sm ${
                  has
                    ? 'border-[color-mix(in_srgb,var(--gold)_32%,var(--line))] bg-gold-soft'
                    : 'border-line bg-surface-2 opacity-40 grayscale'
                }`}
              >
                {b.icon}
              </div>
              <small className="mt-1.5 block text-[10px] font-bold leading-tight text-ink-2">
                {b.name}
              </small>
            </div>
          )
        })}
      </div>

      <div className="mx-4.5 mb-3 mt-6 flex items-center justify-between">
        <h2 className="font-display text-lg font-bold">My reports</h2>
      </div>
      {posts.length === 0 && (
        <p className="px-8 pb-6 text-center text-sm text-ink-3">
          You haven't reported anything yet.
        </p>
      )}
      {posts.map((p) => {
        const chip = statusChip[p.status]
        return (
          <div key={p.id} className="flex items-center gap-3 border-b border-line px-4.5 py-3">
            <img src={p.image_url} alt="" className="size-13 flex-none rounded-xl object-cover" style={{ background: 'var(--surface-2)' }} />
            <div className="flex-1">
              <b className="text-sm font-bold">{severityLabel[p.severity]} severity</b>
              <span className="block text-xs font-semibold text-ink-3">{p.description}</span>
            </div>
            <span className={`rounded-full px-2.5 py-1 text-[10.5px] font-extrabold uppercase ${chip.cls}`}>
              {chip.label}
            </span>
          </div>
        )
      })}
    </>
  )
}
