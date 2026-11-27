import { Eye, EyeOff } from 'lucide-react'
import { forwardRef, type InputHTMLAttributes, useId, useState } from 'react'
import { cn } from '@/lib/utils'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

/** Label + input + inline error, wired for react-hook-form's register(). */
export const FormField = forwardRef<HTMLInputElement, Props>(function FormField(
  { label, error, className, id, type, required = true, ...rest },
  ref,
) {
  const autoId = useId()
  const fieldId = id ?? autoId
  const errorId = `${fieldId}-error`
  const [showPassword, setShowPassword] = useState(false)

  const isPasswordField = type === 'password'
  const resolvedType = isPasswordField
    ? showPassword
      ? 'text'
      : 'password'
    : type

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={fieldId} className="text-[12.5px] font-bold text-ink-2">
        {label}
        {required && 
          <span aria-hidden="true" className="ml-0.5 text-sev-5">*</span>
        }
      </label>

      <div className="relative flex items-center">
        <input
          id={fieldId}
          ref={ref}
          type={resolvedType}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          className={cn(
            'w-full rounded-[14px] border bg-surface px-3.5 py-3.5 text-[15px] text-ink shadow-sm outline-none transition-colors placeholder:text-ink-3 focus:border-brand',
            isPasswordField && 'pr-11',
            error ? 'border-sev-5' : 'border-line-2',
            className,
          )}
          {...rest}
        />

        {isPasswordField && (
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
            className="absolute right-3 inline-flex size-8 items-center justify-center rounded-lg text-ink-3 transition-colors hover:bg-surface-2 hover:text-ink focus:outline-none"
          >
            {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
          </button>
        )}
      </div>

      {error && (
        <span id={errorId} className="text-xs font-medium text-sev-5">
          {error}
        </span>
      )}
    </div>
  )
})