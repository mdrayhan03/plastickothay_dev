import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { apiErrorMessage } from '@/lib/api'
import { forgotSchema, type ForgotInput } from '@/lib/schemas'
import { authService } from '@/services/authService'

export function ForgotPasswordPage() {
  const navigate = useNavigate()
  const form = useForm<ForgotInput>({ resolver: zodResolver(forgotSchema) })

  async function onSubmit(values: ForgotInput) {
    try {
      await authService.forgotPassword(values.username)
      toast.success('If the account exists, a reset code was sent.')
      navigate(`/reset?username=${encodeURIComponent(values.username)}`)
    } catch (e) {
      toast.error(apiErrorMessage(e))
    }
  }

  return (
    <AuthLayout title="Reset your password" subtitle="We'll email you a code to reset it.">
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3">
        <FormField label="Username" error={form.formState.errors.username?.message} {...form.register('username')} />
        <Btn type="submit" loading={form.formState.isSubmitting} className="mt-2">
          Send reset code
        </Btn>
      </form>
      <p className="mt-5 text-center text-sm text-ink-2">
        <Link to="/login" className="font-bold text-brand">
          Back to sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
