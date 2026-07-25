import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { apiErrorMessage } from '@/lib/api'
import { otpSchema, type OtpInput } from '@/lib/schemas'
import { authService } from '@/services/authService'

export function VerifyPage() {
  const [params] = useSearchParams()
  const username = params.get('username') ?? ''
  const navigate = useNavigate()
  const form = useForm<OtpInput>({ resolver: zodResolver(otpSchema) })

  async function onSubmit(values: OtpInput) {
    try {
      await authService.verify(username, Number(values.code))
      toast.success('Account verified — you can sign in now.')
      navigate('/login', { replace: true })
    } catch (e) {
      toast.error(apiErrorMessage(e, 'Verification failed'))
    }
  }

  async function resend() {
    try {
      await authService.resendOtp(username)
      toast.success('A new code is on its way.')
    } catch (e) {
      toast.error(apiErrorMessage(e))
    }
  }

  return (
    <AuthLayout title="Verify your email" subtitle={`Enter the 6-digit code sent to your email.`}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3">
        <FormField
          label="Verification code"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
          className="text-center text-2xl font-bold tracking-[0.4em]"
          error={form.formState.errors.code?.message}
          {...form.register('code')}
        />
        <Btn type="submit" loading={form.formState.isSubmitting} className="mt-2">
          Verify
        </Btn>
      </form>
      <button type="button" onClick={resend} className="mt-5 w-full text-center text-sm font-bold text-brand">
        Didn't get it? Resend code
      </button>
    </AuthLayout>
  )
}
