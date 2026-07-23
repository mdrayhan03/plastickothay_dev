import { formatDistanceToNow } from 'date-fns'
import { Clock, Heart, MapPin } from 'lucide-react'
import { useAuth } from '@/context/auth-context'
import { useLike } from '@/hooks/useLike'
import { cn } from '@/lib/utils'
import { severityClass, severityLabel } from '@/lib/severity'
import type { PublicPost } from '@/types'

export function ReportCard({ post }: { post: PublicPost }) {
  const { status } = useAuth()
  const like = useLike()

  return (
    <article className="mx-4.5 mb-3 flex gap-3 rounded-[20px] border border-line bg-surface p-3 shadow-sm">
      <img
        src={post.image_url}
        alt=""
        loading="lazy"
        className="size-19 flex-none rounded-[14px] object-cover"
        style={{ background: 'var(--surface-2)' }}
      />
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 font-bold">
            <MapPin className="size-3.5 text-ink-3" />
            <span className="truncate">{post.reporter_name || 'Report'}</span>
          </div>
          <span
            className={cn(
              'flex-none rounded-full px-2.5 py-1 text-[11.5px] font-bold text-white',
              severityClass[post.severity],
            )}
          >
            {severityLabel[post.severity]}
          </span>
        </div>
        <p className="line-clamp-2 text-[13px] leading-snug text-ink-2">{post.description}</p>
        <div className="mt-2 flex items-center gap-3.5 text-xs font-semibold text-ink-3">
          <button
            type="button"
            disabled={status !== 'authed' || like.isPending}
            onClick={() => like.mutate({ post })}
            className={cn(
              'inline-flex items-center gap-1.5 transition-colors disabled:opacity-100',
              post.liked_by_me ? 'text-heart' : '',
            )}
          >
            <Heart className="size-[15px]" fill={post.liked_by_me ? 'currentColor' : 'none'} />
            {post.likes}
          </button>
          <span className="inline-flex items-center gap-1.5">
            <Clock className="size-[15px]" />
            {formatDistanceToNow(new Date(post.created), { addSuffix: true })}
          </span>
        </div>
      </div>
    </article>
  )
}
