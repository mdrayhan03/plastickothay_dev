import { zodResolver } from '@hookform/resolvers/zod'
import { BadgeCheck, Save } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { AvatarPicker } from '@/components/AvatarPicker'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { apiErrorMessage } from '@/lib/api'
import { type ProfileInput, profileSchema } from '@/lib/schemas'
import { authService } from '@/services/authService'

export function EditProfilePage() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const [avatar, setAvatar] = useState<string | null>(user?.avatar_url ?? null)

  const form = useForm<ProfileInput>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name ?? '',
      last_name: user?.last_name ?? '',
      phone: user?.phone ?? '',
    },
  })
  const name = `${form.watch('first_name') ?? ''} ${form.watch('last_name') ?? ''}`.trim()

  async function onSubmit(values: ProfileInput) {
    try {
      // Only send the avatar if the user picked a new one (a data URL), not the existing http URL.
      const changedAvatar = avatar && avatar.startsWith('data:') ? avatar : undefined
      const updated = await authService.updateProfile({ ...values, avatar: changedAvatar })
      setUser(updated)
      toast.success('Profile updated')
      navigate('/me')
    } catch (e) {
      toast.error(apiErrorMessage(e))
    }
  }

  return (
    <>
      <TopBar title="Edit profile" back />

      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3 px-4.5 pt-4">
        <AvatarPicker name={name || user?.username} value={avatar} onChange={setAvatar} />
        <FormField label="First name" error={form.formState.errors.first_name?.message} {...form.register('first_name')} />
        <FormField label="Last name" error={form.formState.errors.last_name?.message} {...form.register('last_name')} />
        <FormField label="Phone" type="tel" error={form.formState.errors.phone?.message} {...form.register('phone')} />

        {/* Read-only identity fields — not editable here. */}
        <div className="mt-1 space-y-1.5 rounded-[14px] border border-line bg-surface-2 p-3.5">
          <ReadOnly label="Username" value={user?.username} />
          <ReadOnly
            label="Email"
            value={user?.email}
            badge={user?.is_verified ? 'Verified' : undefined}
          />
          <p className="pt-1 text-[11.5px] text-ink-3">Username and email can’t be changed here.</p>
        </div>

        <Btn type="submit" loading={form.formState.isSubmitting} className="mt-2">
          <Save className="size-5" />
          Save changes
        </Btn>
      </form>
    </>
  )
}

function ReadOnly({ label, value, badge }: { label: string; value?: string; badge?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 text-[13.5px]">
      <span className="font-semibold text-ink-3">{label}</span>
      <span className="flex items-center gap-1.5 truncate font-semibold text-ink">
        {value || '—'}
        {badge && (
          <span className="inline-flex items-center gap-0.5 text-[11px] font-bold text-brand">
            <BadgeCheck className="size-3.5" /> {badge}
          </span>
        )}
      </span>
    </div>
  )
}
