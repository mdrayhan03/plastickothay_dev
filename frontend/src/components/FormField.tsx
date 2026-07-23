import { forwardRef, type InputHTMLAttributes, useId } from 'react'
import { cn } from '@/lib/utils'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

/** Label + input + inline error, wired for react-hook-form's register(). */
export const FormField = forwardRef<HTMLInputElement, Props>(function FormField(
  { label, error, className, id, ...rest },
  ref,
) {
  const autoId = useId()
  const fieldId = id ?? autoId
  const errorId = `${fieldId}-error`
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={fieldId} className="text-[12.5px] font-bold text-ink-2">
        {label}
      </label>
      <input
        id={fieldId}
        ref={ref}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'w-full rounded-[14px] border bg-surface px-3.5 py-3.5 text-[15px] text-ink shadow-sm outline-none transition-colors placeholder:text-ink-3 focus:border-brand',
          error ? 'border-sev-5' : 'border-line-2',
          className,
        )}
        {...rest}
      />
      {error && (
        <span id={errorId} className="text-xs font-medium text-sev-5">
          {error}
        </span>
      )}
    </div>
  )
})
