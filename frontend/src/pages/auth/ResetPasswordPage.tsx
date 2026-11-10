import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { apiErrorMessage } from '@/lib/api'
import { resetSchema, type ResetInput } from '@/lib/schemas'
import { authService } from '@/services/authService'

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const username = params.get('username') ?? ''
  const navigate = useNavigate()
  const form = useForm<ResetInput>({ resolver: zodResolver(resetSchema) })

  async function onSubmit(values: ResetInput) {
    try {
      await authService.resetPassword(username, Number(values.code), values.new_password)
      toast.success('Password reset - sign in with your new password.')
      navigate('/login', { replace: true })
    } catch (e) {
      toast.error(apiErrorMessage(e, 'Reset failed'))
    }
  }

  return (
    <AuthLayout title="Set a new password" subtitle="Enter the code we emailed and your new password.">
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3">
        <FormField
          label="Reset code"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
          className="text-center text-xl font-bold tracking-[0.3em]"
          error={form.formState.errors.code?.message}
          {...form.register('code')}
        />
        <FormField
          label="New password"
          type="password"
          autoComplete="new-password"
          error={form.formState.errors.new_password?.message}
          {...form.register('new_password')}
        />
        <Btn type="submit" loading={form.formState.isSubmitting} className="mt-2">
          Reset password
        </Btn>
      </form>
    </AuthLayout>
  )
}
