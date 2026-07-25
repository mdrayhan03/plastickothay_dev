import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { AvatarPicker } from '@/components/AvatarPicker'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { apiErrorMessage } from '@/lib/api'
import { registerSchema, type RegisterInput } from '@/lib/schemas'
import { authService } from '@/services/authService'

export function RegisterPage() {
  const navigate = useNavigate()
  const [avatar, setAvatar] = useState<string | null>(null)
  const form = useForm<RegisterInput>({ resolver: zodResolver(registerSchema) })
  const name = `${form.watch('first_name') ?? ''} ${form.watch('last_name') ?? ''}`.trim()

  async function onSubmit(values: RegisterInput) {
    try {
      await authService.register({ ...values, avatar: avatar ?? undefined })
      toast.success('Check your email for a verification code.')
      navigate(`/verify?username=${encodeURIComponent(values.username)}`)
    } catch (e) {
      toast.error(apiErrorMessage(e, 'Registration failed'))
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Earn points for every report you make.">
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3">
        <AvatarPicker name={name} value={avatar} onChange={setAvatar} />
        <div className="grid grid-cols-2 gap-3">
          <FormField label="First name" error={form.formState.errors.first_name?.message} {...form.register('first_name')} />
          <FormField label="Last name" error={form.formState.errors.last_name?.message} {...form.register('last_name')} />
        </div>
        <FormField label="Username" autoComplete="username" error={form.formState.errors.username?.message} {...form.register('username')} />
        <FormField label="Email" type="email" autoComplete="email" error={form.formState.errors.email?.message} {...form.register('email')} />
        <FormField label="Phone" type="tel" autoComplete="tel" error={form.formState.errors.phone?.message} {...form.register('phone')} />
        <FormField label="Password" type="password" autoComplete="new-password" error={form.formState.errors.password?.message} {...form.register('password')} />
        <Btn type="submit" loading={form.formState.isSubmitting} className="mt-2">
          Create account
        </Btn>
      </form>
      <p className="mt-5 text-center text-sm text-ink-2">
        Already have an account?{' '}
        <Link to="/login" className="font-bold text-brand">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
