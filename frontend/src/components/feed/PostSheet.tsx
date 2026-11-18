import { formatDistanceToNow } from 'date-fns'
import { Clock, Heart, MapPin, Navigation, User, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'
import { useLike } from '@/hooks/useLike'
import { usePost } from '@/hooks/usePosts'
import { severityClass, severityLabel } from '@/lib/severity'
import { cn } from '@/lib/utils'
import type { PublicPost } from '@/types'

/** Slide-up detail for a map marker (or any post id). */
export function PostSheet({ postId, onClose }: { postId: number | null; onClose: () => void }) {
  const { data: post } = usePost(postId)
  const { status } = useAuth()
  const like = useLike()
  const open = postId != null

  // Keep last loaded post rendered while the 300ms slide-down animation finishes
  const [cachedPost, setCachedPost] = useState<PublicPost | undefined>(post)
  useEffect(() => {
    if (post) setCachedPost(post)
  }, [post])

  const activePost = post ?? (!open ? cachedPost : undefined)

  // Drag-handle state
  const [dragY, setDragY] = useState(0)
  const [dragging, setDragging] = useState(false)
  const startYRef = useRef<number | null>(null)

  useEffect(() => {
    if (open) {
      setDragY(0)
      setDragging(false)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    // Ignore clicks on the close button itself
    if ((e.target as HTMLElement).closest('button')) return
    startYRef.current = e.clientY
    setDragging(true)
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (startYRef.current == null) return
    const delta = Math.max(0, e.clientY - startYRef.current)
    setDragY(delta)
  }

  const handlePointerUp = () => {
    if (startYRef.current == null) return
    const shouldClose = dragY > 90
    startYRef.current = null
    setDragging(false)
    if (shouldClose) {
      onClose()
    } else {
      setDragY(0)
    }
  }

  return (
    <>
      <div
        className={cn(
          'fixed inset-0 z-[600] bg-black/40 transition-opacity duration-300',
          open ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-hidden={!open}
        aria-label="Report details"
        style={{
          transform: open ? (dragY > 0 ? `translateY(${dragY}px)` : 'translateY(0)') : 'translateY(100%)',
        }}
        className={cn(
          'fixed inset-x-0 bottom-0 z-[601] flex max-h-[85vh] w-full flex-col rounded-t-3xl bg-surface shadow-[0_-16px_40px_-16px_rgba(10,33,28,.4)] md:max-h-[88vh]',
          !dragging && 'transition-transform duration-300 ease-out',
          !open && 'pointer-events-none',
        )}
      >
        {/* Draggable Top Handle & Close Header */}
        <div
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          className="relative flex flex-none cursor-grab touch-none select-none items-center justify-center border-b border-line/60 pb-3 pt-3 active:cursor-grabbing"
        >
          <span className="h-1.5 w-10 rounded-full bg-line-2" />
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="absolute right-3 top-2.5 grid size-8 place-items-center rounded-full bg-surface-2 text-ink-2 transition-colors hover:text-ink"
          >
            <X className="size-4.5" />
          </button>
        </div>

        {activePost ? (
          <>
            {/* Scrollable Body: Stacked on Phone, Split Left-Image / Right-Details on Desktop */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:gap-6">
                {/* Left on Desktop / Top on Phone: Image */}
                <div
                  className="flex w-full shrink-0 items-center justify-center overflow-hidden rounded-2xl md:sticky md:top-0 md:w-[44%] lg:w-[40%]"
                  style={{ background: 'var(--surface-2)' }}
                >
                  <img
                    src={activePost.image_url}
                    alt={activePost.place_name || 'Report photo'}
                    className="max-h-72 w-full object-contain md:max-h-[56vh]"
                  />
                </div>

                {/* Right on Desktop / Bottom on Phone: Location + Severity, User + Time, Description */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-1.5 font-bold md:text-lg">
                      <MapPin className="size-4 shrink-0 text-brand md:size-5" />
                      <span className="truncate">{activePost.place_name || 'Report'}</span>
                    </div>
                    <span
                      className={cn(
                        'flex-none rounded-full px-2.5 py-1 text-[11.5px] font-bold text-white md:px-3 md:text-xs',
                        severityClass[activePost.severity],
                      )}
                    >
                      {severityLabel[activePost.severity]}
                    </span>
                  </div>

                  <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] font-semibold text-ink-3">
                    {activePost.reporter_id ? (
                      <Link
                        to={`/u/${activePost.reporter_id}`}
                        onClick={onClose}
                        className="inline-flex min-w-0 items-center gap-1.5 text-brand hover:underline"
                      >
                        <User className="size-4 shrink-0" />
                        <span className="truncate">{activePost.reporter_name}</span>
                      </Link>
                    ) : (
                      <span className="inline-flex min-w-0 items-center gap-1.5 text-ink-3">
                        <User className="size-4 shrink-0" />
                        <span className="truncate">Anonymous</span>
                      </span>
                    )}

                    <span className="inline-flex shrink-0 items-center gap-1.5">
                      <Clock className="size-4" />
                      {formatDistanceToNow(new Date(activePost.created), { addSuffix: true })}
                    </span>
                  </div>

                  {activePost.description && (
                    <p className="mt-3.5 whitespace-pre-line break-words text-[14px] leading-relaxed text-ink-2 md:text-[15px]">
                      {activePost.description}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Sticky Bottom Action Bar */}
            <div className="flex flex-none items-center gap-3 border-t border-line/60 bg-surface px-4 py-3 md:px-6">
              <button
                type="button"
                disabled={status !== 'authed' || like.isPending}
                onClick={() => like.mutate({ post: activePost })}
                className={cn(
                  'inline-flex shrink-0 items-center gap-1.5 rounded-[14px] border border-line-2 px-4 py-3 text-sm font-bold text-ink-2 transition-colors disabled:opacity-60',
                  activePost.liked_by_me && 'border-heart/30 bg-heart/10 text-heart',
                )}
              >
                <Heart className="size-4.5" fill={activePost.liked_by_me ? 'currentColor' : 'none'} />
                {activePost.likes}
              </button>

              <a
                href={`https://www.google.com/maps/search/?api=1&query=${activePost.lat},${activePost.lon}`}
                target="_blank"
                rel="noreferrer"
                className="flex flex-1 items-center justify-center gap-2 rounded-[14px] border border-line-2 bg-surface py-3 text-sm font-bold text-ink shadow-sm transition-colors hover:bg-surface-2"
              >
                <Navigation className="size-4.5 text-brand" />
                Directions
              </a>
            </div>
          </>
        ) : (
          open && <div className="m-4 h-64 animate-pulse rounded-2xl bg-surface-2" />
        )}
      </div>
    </>
  )
}