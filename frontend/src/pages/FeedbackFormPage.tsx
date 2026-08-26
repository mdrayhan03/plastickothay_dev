import { zodResolver } from '@hookform/resolvers/zod'
import { Send, Star } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { apiErrorMessage } from '@/lib/api'
import { type FeedbackInput, feedbackSchema } from '@/lib/schemas'
import { cn } from '@/lib/utils'
import { contentService } from '@/services/contentService'

const RATING_LABEL = ['', 'Poor', 'Fair', 'Good', 'Great', 'Love it!']

export function FeedbackFormPage() {
  const { user } = useAuth()
  const form = useForm<FeedbackInput>({
    resolver: zodResolver(feedbackSchema),
    defaultValues: { rating: 0, comment: '', name: '', email: '' },
  })
  const rating = form.watch('rating')

  useEffect(() => {
    if (user)
      form.reset((v) => ({ ...v, name: `${user.first_name} ${user.last_name}`.trim(), email: user.email }))
  }, [user, form])

  async function onSubmit(values: FeedbackInput) {
    try {
      await contentService.submitFeedback({
        rating: values.rating,
        comment: values.comment,
        name: values.name,
        email: values.email || undefined,
      })
      toast.success('Thanks for your feedback! 💚')
      form.reset({ rating: 0, comment: '', name: values.name, email: values.email })
    } catch (e) {
      toast.error(apiErrorMessage(e))
    }
  }

  return (
    <>
      <TopBar title="Rate us" />

      <div className="px-4.5 pb-6 pt-4">
        <h1 className="font-display text-xl font-extrabold">How are we doing?</h1>
        <p className="mt-1 text-sm text-ink-2">Your feedback shapes PlasticKothay.</p>

        <form onSubmit={form.handleSubmit(onSubmit)} className="mt-5 flex flex-col gap-4">
          <div className="rounded-[18px] border border-line bg-surface p-5 text-center shadow-sm">
            <div className="flex justify-center gap-2">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  aria-label={`${n} star${n > 1 ? 's' : ''}`}
                  aria-pressed={rating >= n}
                  onClick={() => form.setValue('rating', n, { shouldValidate: true })}
                  className="transition-transform active:scale-90"
                >
                  <Star
                    className={cn('size-9', rating >= n ? 'text-gold' : 'text-line-2')}
                    fill={rating >= n ? 'var(--gold)' : 'none'}
                    strokeWidth={1.6}
                  />
                </button>
              ))}
            </div>
            <div className="mt-2 h-5 text-[13px] font-bold text-gold">{RATING_LABEL[rating]}</div>
            {form.formState.errors.rating && (
              <span className="text-xs font-medium text-sev-5">{form.formState.errors.rating.message}</span>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[12.5px] font-bold text-ink-2">Comment (optional)</label>
            <textarea
              {...form.register('comment')}
              placeholder="What did you like, or what could be better?"
              className="min-h-28 w-full resize-none rounded-[14px] border border-line-2 bg-surface p-3.5 text-[15px] shadow-sm outline-none focus:border-brand"
            />
          </div>

          {!user && (
            <div className="flex flex-col gap-3">
              <FormField label="Name (optional)" {...form.register('name')} />
              <FormField label="Email (optional)" type="email" error={form.formState.errors.email?.message} {...form.register('email')} />
            </div>
          )}

          <Btn type="submit" loading={form.formState.isSubmitting} className="mt-1">
            <Send className="size-5" />
            Send feedback
          </Btn>
        </form>
      </div>
    </>
  )
}
