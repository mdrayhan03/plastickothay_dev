import { formatDistanceToNow } from 'date-fns'
import { Clock, Heart, MapPin, User } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'
import { useLike } from '@/hooks/useLike'
import { cn } from '@/lib/utils'
import { severityClass, severityLabel } from '@/lib/severity'
import type { PublicPost } from '@/types'

export function ReportCard({ post, onOpen }: { post: PublicPost; onOpen?: (id: number) => void }) {
  const { status } = useAuth()
  const like = useLike()

  return (
    <article className="flex w-full min-w-0 flex-col gap-2.5 overflow-hidden rounded-[20px] border border-line bg-surface p-3 shadow-sm">
      <div className="flex min-w-0 gap-3">
        <button
          type="button"
          onClick={() => onOpen?.(post.id)}
          aria-label={`Open report ${post.id}`}
          className="flex-none"
        >
          <img
            src={post.image_url}
            alt=""
            loading="lazy"
            className="size-19 rounded-[14px] object-cover"
            style={{ background: 'var(--surface-2)' }}
          />
        </button>

        <div className="min-w-0 flex-1">
          <button
            type="button"
            onClick={() => onOpen?.(post.id)}
            className="block w-full min-w-0 overflow-hidden text-left"
          >
            <div className="mb-1 flex min-w-0 items-center justify-between gap-2">
              <div className="flex min-w-0 flex-1 items-center gap-1.5 font-bold">
                <MapPin className="size-3.5 shrink-0 text-ink-3" />
                <span className="truncate">{post.place_name || 'Report'}</span>
              </div>
              <span
                className={cn(
                  'shrink-0 rounded-full px-2.5 py-1 text-[11.5px] font-bold text-white',
                  severityClass[post.severity],
                )}
              >
                {severityLabel[post.severity]}
              </span>
            </div>
            <p className="line-clamp-2 break-words text-[13px] leading-snug text-ink-2">
              {post.description}
            </p>
          </button>
        </div>
      </div>

      <div className="flex w-full min-w-0 items-center gap-3 border-t border-line/60 pt-2 text-xs font-semibold text-ink-3">
        <button
          type="button"
          disabled={status !== 'authed' || like.isPending}
          onClick={() => like.mutate({ post })}
          className={cn(
            'inline-flex shrink-0 items-center gap-1.5 transition-colors disabled:opacity-100',
            post.liked_by_me ? 'text-heart' : '',
          )}
        >
          <Heart className="size-[15px]" fill={post.liked_by_me ? 'currentColor' : 'none'} />
          {post.likes}
        </button>

        <span className="inline-flex shrink-0 items-center gap-1.5">
          <Clock className="size-[15px]" />
          {formatDistanceToNow(new Date(post.created), { addSuffix: true })}
        </span>

        {post.reporter_id ? (
          <Link
            to={`/u/${post.reporter_id}`}
            className="ml-auto inline-flex min-w-0 items-center gap-1 text-brand hover:underline"
          >
            <User className="size-[14px] shrink-0" />
            <span className="truncate">{post.reporter_name || 'Anonymous'}</span>
          </Link>
        ) : (
          <span className="ml-auto inline-flex min-w-0 items-center gap-1 text-ink-3">
            <User className="size-[14px] shrink-0" />
            <span className="truncate">{post.reporter_name || 'Anonymous'}</span>
          </span>
        )}
      </div>
    </article>
  )
}