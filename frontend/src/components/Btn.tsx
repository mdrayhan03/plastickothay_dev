import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost'
  loading?: boolean
  children: ReactNode
}

/** The app's primary CTA — the gradient button from the prototype. */
export function Btn({ variant = 'primary', loading, disabled, className, children, ...rest }: Props) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'flex h-13 w-full items-center justify-center gap-2 rounded-[14px] text-[15.5px] font-bold transition-transform active:translate-y-px disabled:opacity-60',
        variant === 'primary'
          ? 'bg-[linear-gradient(152deg,var(--brand-2),var(--brand-deep))] text-white shadow-[0_8px_18px_-8px_color-mix(in_srgb,var(--brand)_70%,transparent)]'
          : 'border border-line-2 bg-surface text-ink shadow-sm',
        className,
      )}
      {...rest}
    >
      {loading ? <span className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : children}
    </button>
  )
}
