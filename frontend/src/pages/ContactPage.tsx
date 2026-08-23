import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { Mail, MapPin, Phone, Send } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { apiErrorMessage } from '@/lib/api'
import { qk } from '@/lib/queryClient'
import { type ContactInput, contactSchema } from '@/lib/schemas'
import { contentService } from '@/services/contentService'

export function ContactPage() {
  const { user } = useAuth()
  const { data: page } = useQuery({ queryKey: qk.contactPage, queryFn: contentService.contactPage })

  const form = useForm<ContactInput>({
    resolver: zodResolver(contactSchema),
    defaultValues: { name: '', email: '', phone: '', subject: '', message: '' },
  })
  const { reset } = form

  useEffect(() => {
    if (user)
      reset((v) => ({
        ...v,
        name: `${user.first_name} ${user.last_name}`.trim(),
        email: user.email,
        phone: user.phone || '',
      }))
  }, [user, reset])

  async function onSubmit(values: ContactInput) {
    try {
      await contentService.submitContactMessage(values)
      toast.success('Message sent - we’ll get back to you.')
      form.reset({ ...values, subject: '', message: '' })
    } catch (e) {
      toast.error(apiErrorMessage(e))
    }
  }

  const details = [
    page?.email && { icon: Mail, label: page.email, href: `mailto:${page.email}` },
    page?.phone && { icon: Phone, label: page.phone, href: `tel:${page.phone}` },
    page?.address && { icon: MapPin, label: page.address },
  ].filter(Boolean) as { icon: typeof Mail; label: string; href?: string }[]

  return (
    <>
      <TopBar title="Contact us" />

      <div className="px-4.5 pb-6 pt-4">
        <h1 className="font-display text-xl font-extrabold">{page?.heading || 'Get in touch'}</h1>
        {page?.intro && <p className="mt-1 text-sm text-ink-2">{page.intro}</p>}

        {details.length > 0 && (
          <div className="mt-4 space-y-2 rounded-[18px] border border-line bg-surface p-4 shadow-sm">
            {details.map((d, i) => {
              const inner = (
                <>
                  <span className="grid size-9 flex-none place-items-center rounded-[11px] bg-brand-soft text-brand-deep">
                    <d.icon className="size-[18px]" />
                  </span>
                  <span className="text-[13.5px] font-semibold text-ink">{d.label}</span>
                </>
              )
              return d.href ? (
                <a key={i} href={d.href} className="flex items-center gap-3">
                  {inner}
                </a>
              ) : (
                <div key={i} className="flex items-center gap-3">
                  {inner}
                </div>
              )
            })}
          </div>
        )}

        <form onSubmit={form.handleSubmit(onSubmit)} className="mt-5 flex flex-col gap-3">
          <FormField label="Your name" error={form.formState.errors.name?.message} {...form.register('name')} />
          <FormField label="Email" type="email" error={form.formState.errors.email?.message} {...form.register('email')} />
          <FormField label="Phone (optional)" type="tel" error={form.formState.errors.phone?.message} {...form.register('phone')} />
          <FormField label="Subject" error={form.formState.errors.subject?.message} {...form.register('subject')} />
          <div className="flex flex-col gap-2">
            <label htmlFor="contact-message" className="text-[12.5px] font-bold text-ink-2">
              Message
            </label>
            <textarea
              id="contact-message"
              {...form.register('message')}
              placeholder="How can we help?"
              className="min-h-28 w-full resize-none rounded-[14px] border border-line-2 bg-surface p-3.5 text-[15px] shadow-sm outline-none focus:border-brand"
            />
            {form.formState.errors.message && (
              <span className="text-xs font-medium text-sev-5">{form.formState.errors.message.message}</span>
            )}
          </div>
          <Btn type="submit" loading={form.formState.isSubmitting} className="mt-2">
            <Send className="size-5" />
            Send message
          </Btn>
        </form>
      </div>
    </>
  )
}
