import { UserX } from 'lucide-react'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Avatar } from '@/components/Avatar'
import { PostSheet } from '@/components/feed/PostSheet'
import { ReportCard } from '@/components/feed/ReportCard'
import { TopBar } from '@/components/layout/TopBar'
import { usePublicProfile, useUserPosts } from '@/hooks/useUser'

export function ProfilePage() {
  const { id } = useParams()
  const userId = Number(id)
  const { data: profile, isLoading, isError } = usePublicProfile(userId)
  const posts = useUserPosts(userId)
  const [selected, setSelected] = useState<number | null>(null)

  const allPosts = posts.data?.pages.flatMap((p) => p.results) ?? []

  return (
    <>
      <TopBar title="Profile" back />

      {isLoading && <div className="mx-4.5 mt-6 h-40 animate-pulse rounded-2xl bg-surface-2" />}

      {isError && (
        <div className="mx-4.5 mt-6 grid place-items-center rounded-2xl border border-line bg-surface p-12 text-center">
          <UserX className="mb-3 size-8 text-ink-3" />
          <div className="font-bold text-ink">Profiles aren’t available yet</div>
          <p className="mt-1 max-w-xs text-sm text-ink-2">
            Public user profiles need the <b>/api/users/&lt;id&gt;/</b> endpoint (BE-10). It’s
            planned - this screen lights up once it ships.
          </p>
        </div>
      )}

      {profile && (
        <>
          <div className="flex flex-col items-center px-4.5 pb-2 pt-6 text-center">
            <Avatar name={profile.full_name || profile.username} src={profile.avatar_url} className="size-24 text-3xl" />
            <div className="mt-3 font-display text-[22px] font-bold">{profile.full_name || profile.username}</div>
            <div className="text-[13px] font-semibold text-ink-3">@{profile.username}</div>
            <div className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-brand-soft px-3 py-1 text-xs font-extrabold text-brand-deep">
              Lvl {profile.level} {profile.level_title ? `· ${profile.level_title}` : ''}
            </div>

            <div className="mt-4 grid w-full grid-cols-4 gap-2">
              {[
                { n: `Lvl ${profile.level}`, l: 'Level' },
                { n: profile.posts_approved.toLocaleString(), l: 'Reports' },
                { n: profile.likes_received.toLocaleString(), l: 'Likes' },
                { n: profile.total_points.toLocaleString(), l: 'Points', reward: true },
              ].map((s) => (
                <div key={s.l} className="rounded-[16px] border border-line bg-surface p-2.5 text-center shadow-sm">
                  <b className={`block font-display text-base leading-none tnum ${s.reward ? 'text-gold' : ''}`}>
                    {s.n}
                  </b>
                  <span className="mt-1 block text-[10px] font-bold uppercase tracking-wide text-ink-2">{s.l}</span>
                </div>
              ))}
            </div>
          </div>

          {profile.badges.length > 0 && (
            <>
              <h2 className="mx-4.5 mb-3 mt-6 font-display text-lg font-bold">Badges</h2>
              <div className="grid grid-cols-4 gap-3 px-4.5">
                {profile.badges.map((b) => (
                  <div key={b.code} className="text-center">
                    <div className="grid aspect-square place-items-center rounded-[18px] border border-[color-mix(in_srgb,var(--gold)_32%,var(--line))] bg-gold-soft text-[26px] shadow-sm">
                      {b.icon}
                    </div>
                    <small className="mt-1.5 block text-[10px] font-bold leading-tight text-ink-2">{b.name}</small>
                  </div>
                ))}
              </div>
            </>
          )}

          <h2 className="mx-4.5 mb-3 mt-6 font-display text-lg font-bold">Reports</h2>
          {posts.isError && (
            <p className="px-8 pb-4 text-center text-[12.5px] text-ink-3">
              This user’s reports need the <b>/api/users/&lt;id&gt;/posts/</b> endpoint (BE-10).
            </p>
          )}
          {!posts.isError && allPosts.length === 0 && !posts.isLoading && (
            <p className="px-8 pb-6 text-center text-sm text-ink-3">No public reports yet.</p>
          )}
          <div className="grid gap-3 px-4.5 md:grid-cols-2">
            {allPosts.map((post) => (
              <ReportCard key={post.id} post={post} onOpen={setSelected} />
            ))}
          </div>
          {posts.hasNextPage && (
            <button
              type="button"
              onClick={() => posts.fetchNextPage()}
              disabled={posts.isFetchingNextPage}
              className="mx-4.5 my-2 block w-[calc(100%-2.25rem)] rounded-[14px] border border-line-2 bg-surface py-3 text-sm font-bold text-ink shadow-sm"
            >
              {posts.isFetchingNextPage ? 'Loading…' : 'Load more'}
            </button>
          )}
        </>
      )}

      <PostSheet postId={selected} onClose={() => setSelected(null)} />
    </>
  )
}
