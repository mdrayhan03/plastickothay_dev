import { formatDistanceToNow } from 'date-fns'
import { ArrowUpDown, Clock, Heart, MapPin, Moon, Pencil } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PostSheet } from '@/components/feed/PostSheet'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { useOwnPosts } from '@/hooks/usePosts'
import { useBadges, useContribution } from '@/hooks/useScoring'
import { useTheme } from '@/hooks/useTheme'
import { severityClass, severityLabel } from '@/lib/severity'
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
  const rawPosts = own.data?.pages.flatMap((p) => p.results) ?? []
  const earned = new Set(badges?.map((b) => b.code))

  const [statusFilter, setStatusFilter] = useState<'all' | PostStatus>('all')
  const [sortOrder, setSortOrder] = useState<'latest' | 'oldest'>('latest')
  const [selectedPostId, setSelectedPostId] = useState<number | null>(null)

  // Status Counts
  const counts = useMemo(
    () => ({
      all: rawPosts.length,
      approved: rawPosts.filter((p) => p.status === 1).length,
      pending: rawPosts.filter((p) => p.status === 2).length,
      rejected: rawPosts.filter((p) => p.status === 0).length,
    }),
    [rawPosts],
  )

  // Filtered & Sorted Timeline Posts
  const filteredPosts = useMemo(() => {
    let result = [...rawPosts]
    if (statusFilter !== 'all') {
      result = result.filter((p) => p.status === statusFilter)
    }
    result.sort((a, b) => {
      const timeA = new Date(a.created).getTime()
      const timeB = new Date(b.created).getTime()
      return sortOrder === 'latest' ? timeB - timeA : timeA - timeB
    })
    return result
  }, [rawPosts, statusFilter, sortOrder])

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

      {/* --- Timeline / My Reports Header --- */}
      <div className="mx-4.5 mb-3 mt-7 flex items-center justify-between">
        <div>
          <h2 className="font-display text-lg font-bold">My reports timeline</h2>
          <p className="text-xs font-semibold text-ink-3">Your pollution reports from latest to oldest</p>
        </div>

        <button
          type="button"
          onClick={() => setSortOrder((prev) => (prev === 'latest' ? 'oldest' : 'latest'))}
          className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-bold text-ink shadow-sm transition hover:bg-surface-2"
        >
          <ArrowUpDown className="size-3.5 text-brand" />
          <span>{sortOrder === 'latest' ? 'Latest first' : 'Oldest first'}</span>
        </button>
      </div>

      {/* --- Filter Pills Bar --- */}
      <div className="no-scrollbar flex gap-2 overflow-x-auto px-4.5 pb-3">
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
              onClick={() => setStatusFilter(item.id as 'all' | PostStatus)}
              className={`flex flex-none items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-bold transition ${
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

      {/* --- Timeline Feed Posts (Facebook Profile Style) --- */}
      {filteredPosts.length === 0 ? (
        <div className="mx-4.5 my-4 rounded-2xl border border-dashed border-line bg-surface-2 p-8 text-center">
          <p className="text-sm font-semibold text-ink-3">No reports found matching this filter.</p>
        </div>
      ) : (
        <div className="space-y-4 px-4.5 pb-6">
          {filteredPosts.map((p) => {
            const chip = statusChip[p.status]
            return (
              <div
                key={p.id}
                onClick={() => setSelectedPostId(p.id)}
                className="group cursor-pointer overflow-hidden rounded-2xl border border-line bg-surface p-4 shadow-sm transition hover:border-brand-soft"
              >
                {/* Header */}
                <div className="flex items-center justify-between pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="grid size-9 place-items-center rounded-full bg-brand-soft font-display font-bold text-brand-deep">
                      {user?.first_name?.[0] || 'Y'}
                    </div>
                    <div>
                      <b className="block text-sm font-bold text-ink">
                        {user ? `${user.first_name} ${user.last_name}` : 'You'}
                      </b>
                      <span className="flex items-center gap-1 text-[11px] font-medium text-ink-3">
                        <Clock className="size-3" />
                        {formatDistanceToNow(new Date(p.created), { addSuffix: true })}
                      </span>
                    </div>
                  </div>

                  <span className={`rounded-full px-2.5 py-1 text-[10.5px] font-extrabold uppercase ${chip.cls}`}>
                    {chip.label}
                  </span>
                </div>

                {/* Cover Image */}
                <div className="relative overflow-hidden rounded-xl bg-surface-2">
                  <img
                    src={p.image_url}
                    alt=""
                    className="h-44 w-full object-cover transition duration-300 group-hover:scale-105"
                  />
                  <span
                    className={`absolute right-2.5 top-2.5 rounded-full px-2.5 py-1 text-[10.5px] font-bold text-white shadow-md ${severityClass[p.severity]}`}
                  >
                    {severityLabel[p.severity]} severity
                  </span>
                </div>

                {/* Content Details */}
                <div className="pt-3">
                  {p.place_name && (
                    <div className="flex items-center gap-1.5 text-xs font-bold text-brand">
                      <MapPin className="size-3.5 flex-none" />
                      <span className="truncate">{p.place_name}</span>
                    </div>
                  )}
                  {p.description && (
                    <p className="mt-1 line-clamp-2 text-xs font-medium leading-relaxed text-ink-2">
                      {p.description}
                    </p>
                  )}

                  {/* Actions Footer */}
                  <div className="mt-3 flex items-center justify-between border-t border-line pt-2.5 text-xs font-semibold text-ink-3">
                    <span className="flex items-center gap-1.5">
                      <Heart className="size-4 text-heart" fill={p.liked_by_me ? 'currentColor' : 'none'} />
                      {p.likes} {p.likes === 1 ? 'like' : 'likes'}
                    </span>
                    <span className="text-brand font-bold">View details →</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* --- Detail Slide-Up Modal --- */}
      <PostSheet postId={selectedPostId} onClose={() => setSelectedPostId(null)} />
    </>
  )
}

