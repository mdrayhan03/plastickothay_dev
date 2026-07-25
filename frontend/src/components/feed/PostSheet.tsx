import { formatDistanceToNow } from 'date-fns'
import { Clock, Heart, MapPin, Navigation, X } from 'lucide-react'
import { useEffect } from 'react'
import { useAuth } from '@/context/auth-context'
import { useLike } from '@/hooks/useLike'
import { usePost } from '@/hooks/usePosts'
import { severityClass, severityLabel } from '@/lib/severity'
import { cn } from '@/lib/utils'

/** Slide-up detail for a map marker (or any post id). */
export function PostSheet({ postId, onClose }: { postId: number | null; onClose: () => void }) {
  const { data: post } = usePost(postId)
  const { status } = useAuth()
  const like = useLike()
  const open = postId != null

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <>
      <div
        className={cn(
          'absolute inset-0 z-[600] bg-black/40 transition-opacity',
          open ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Report details"
        className={cn(
          'absolute inset-x-0 bottom-0 z-[601] max-h-[85%] overflow-y-auto rounded-t-3xl bg-surface shadow-[0_-16px_40px_-16px_rgba(10,33,28,.4)] transition-transform duration-300',
          open ? 'translate-y-0' : 'translate-y-full',
        )}
      >
        <div className="sticky top-0 flex justify-center bg-surface pt-3">
          <span className="h-1.5 w-10 rounded-full bg-line-2" />
          <button
            onClick={onClose}
            aria-label="Close"
            className="absolute right-3 top-2.5 grid size-8 place-items-center rounded-full bg-surface-2 text-ink-2"
          >
            <X className="size-4.5" />
          </button>
        </div>

        {post && (
          <div className="p-4">
            <img
              src={post.image_url}
              alt=""
              className="h-56 w-full rounded-2xl object-cover"
              style={{ background: 'var(--surface-2)' }}
            />
            <div className="mt-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 font-bold">
                <MapPin className="size-4 text-brand" />
                <span className="truncate">{post.place_name || post.reporter_name || 'Report'}</span>
              </div>
              <span className={cn('flex-none rounded-full px-2.5 py-1 text-[11.5px] font-bold text-white', severityClass[post.severity])}>
                {severityLabel[post.severity]}
              </span>
            </div>

            {post.description && <p className="mt-2 text-[14px] leading-relaxed text-ink-2">{post.description}</p>}

            <div className="mt-3 flex items-center gap-4 text-[13px] font-semibold text-ink-3">
              <button
                type="button"
                disabled={status !== 'authed' || like.isPending}
                onClick={() => like.mutate({ post })}
                className={cn('inline-flex items-center gap-1.5', post.liked_by_me && 'text-heart')}
              >
                <Heart className="size-[17px]" fill={post.liked_by_me ? 'currentColor' : 'none'} />
                {post.likes}
              </button>
              <span className="inline-flex items-center gap-1.5">
                <Clock className="size-[17px]" />
                {formatDistanceToNow(new Date(post.created), { addSuffix: true })}
              </span>
            </div>

            <a
              href={`https://www.google.com/maps/search/?api=1&query=${post.lat},${post.lon}`}
              target="_blank"
              rel="noreferrer"
              className="mt-4 flex items-center justify-center gap-2 rounded-[14px] border border-line-2 bg-surface py-3 text-sm font-bold text-ink shadow-sm"
            >
              <Navigation className="size-4.5 text-brand" />
              Directions
            </a>
          </div>
        )}

        {open && !post && <div className="m-4 h-56 animate-pulse rounded-2xl bg-surface-2" />}
      </div>
    </>
  )
}
