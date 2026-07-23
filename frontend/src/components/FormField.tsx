import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

/** Label + input + inline error, wired for react-hook-form's register(). */
export const FormField = forwardRef<HTMLInputElement, Props>(function FormField(
  { label, error, className, ...rest },
  ref,
) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-[12.5px] font-bold text-ink-2">{label}</label>
      <input
        ref={ref}
        className={cn(
          'w-full rounded-[14px] border bg-surface px-3.5 py-3.5 text-[15px] text-ink shadow-sm outline-none transition-colors placeholder:text-ink-3 focus:border-brand',
          error ? 'border-sev-5' : 'border-line-2',
          className,
        )}
        {...rest}
      />
      {error && <span className="text-xs font-medium text-sev-5">{error}</span>}
    </div>
  )
})
