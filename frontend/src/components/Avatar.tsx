import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

function initials(name?: string) {
  return (name ?? '')
    .split(' ')
    .map((n) => n[0])
    .filter(Boolean)
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

/** Avatar: shows the uploaded/external photo when present and loaded, otherwise a gradient initials circle. */
export function Avatar({
  name,
  src,
  className,
}: {
  name?: string
  src?: string | null
  className?: string
}) {
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    setFailed(false)
  }, [src])

  const base = cn('grid place-items-center overflow-hidden rounded-full text-white', className)

  if (src && !failed) {
    return (
      <img
        src={src}
        alt={name ?? ''}
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
        className={cn(base, 'object-cover')}
      />
    )
  }

  return (
    <span
      className={base}
      style={{ background: 'linear-gradient(135deg,var(--brand-2),var(--brand-deep))' }}
    >
      <span className="font-extrabold">{initials(name) || '?'}</span>
    </span>
  )
}