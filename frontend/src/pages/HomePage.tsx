import { Bell, MapPin, Moon, Sun } from 'lucide-react'
import { useState } from 'react'
import { PostSheet } from '@/components/feed/PostSheet'
import { ReportCard } from '@/components/feed/ReportCard'
import { LazyMap } from '@/components/map/LazyMap'
import { useAuth } from '@/context/auth-context'
import { usePostFeed, useMapMarkers } from '@/hooks/usePosts'
import { useSiteConfig } from '@/hooks/useSiteConfig'
import { useTheme } from '@/hooks/useTheme'

export function HomePage() {
  const { data: config } = useSiteConfig()
  const { user, status } = useAuth()
  const { theme, toggle } = useTheme()
  const { data: markers } = useMapMarkers()
  const feed = usePostFeed()
  const [selected, setSelected] = useState<number | null>(null)

  const center: [number, number] = config?.map_center
    ? [config.map_center.lat, config.map_center.lon]
    : [23.8103, 90.4125]
  const posts = feed.data?.pages.flatMap((p) => p.results) ?? []

  return (
    <>
      <div className="flex items-center justify-between px-4.5 pb-2 pt-3.5">
        <div>
          <div className="text-[13px] font-semibold text-ink-2">
            {status === 'authed' && user ? `Welcome, ${user.first_name} 👋` : 'Welcome 👋'}
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 font-display text-[22px] font-bold tracking-[-0.02em]">
            <MapPin className="size-[18px] text-brand" />
            {config?.site_name?.includes('Dhaka') ? config.site_name : 'Dhaka'}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={toggle}
            aria-label="Toggle theme"
            className="grid size-10 place-items-center rounded-[13px] bg-surface text-ink shadow-sm active:scale-95"
          >
            {theme === 'dark' ? <Sun className="size-5" /> : <Moon className="size-5" />}
          </button>
          <button
            type="button"
            aria-label="Notifications"
            className="grid size-10 place-items-center rounded-[13px] bg-surface text-ink shadow-sm active:scale-95"
          >
            <Bell className="size-5" />
          </button>
        </div>
      </div>

      {/* map */}
      <div className="relative mx-4.5 mt-2 h-75 overflow-hidden rounded-3xl border border-line shadow-md">
        <LazyMap
          center={center}
          zoom={config?.map_zoom ?? 12}
          markers={markers ?? []}
          onMarkerClick={setSelected}
        />
        <div className="absolute right-3 top-3 z-[500] rounded-2xl border border-line bg-[color-mix(in_srgb,var(--surface)_90%,transparent)] px-3 py-2 shadow-sm backdrop-blur">
          <b className="block font-display text-lg leading-none tnum">{markers?.length ?? 0}</b>
          <span className="text-[10px] font-bold uppercase tracking-wide text-ink-2">on map</span>
        </div>
      </div>

      {/* feed */}
      <div className="mx-4.5 mb-3 mt-5.5 flex items-center justify-between">
        <h2 className="font-display text-lg font-bold">Recent reports</h2>
      </div>

      {feed.isLoading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="mx-4.5 h-25 animate-pulse rounded-[20px] bg-surface-2" />
          ))}
        </div>
      )}

      {!feed.isLoading && posts.length === 0 && (
        <p className="px-8 py-10 text-center text-sm text-ink-3">
          No approved reports yet. Be the first — tap the + button.
        </p>
      )}

      {posts.map((post) => (
        <ReportCard key={post.id} post={post} />
      ))}

      {feed.hasNextPage && (
        <button
          type="button"
          onClick={() => feed.fetchNextPage()}
          disabled={feed.isFetchingNextPage}
          className="mx-4.5 my-2 block w-[calc(100%-2.25rem)] rounded-[14px] border border-line-2 bg-surface py-3 text-sm font-bold text-ink shadow-sm"
        >
          {feed.isFetchingNextPage ? 'Loading…' : 'Load more'}
        </button>
      )}

      <PostSheet postId={selected} onClose={() => setSelected(null)} />
    </>
  )
}
