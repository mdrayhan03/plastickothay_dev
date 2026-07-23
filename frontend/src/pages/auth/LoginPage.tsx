import { zodResolver } from '@hookform/resolvers/zod'
import { Send } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { useAuth } from '@/context/auth-context'
import { apiErrorMessage } from '@/lib/api'
import { loginSchema, type LoginInput } from '@/lib/schemas'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string })?.from ?? '/'
  const form = useForm<LoginInput>({ resolver: zodResolver(loginSchema) })

  async function onSubmit(values: LoginInput) {
    try {
      await login(values.username, values.password)
      navigate(from, { replace: true })
    } catch (e) {
      toast.error(apiErrorMessage(e, 'Sign in failed'))
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Map plastic pollution. Clean up your city, together."
      footer={
        <Link to="/" className="flex items-center justify-center gap-2 text-sm font-bold text-ink">
          <Send className="size-4.5 text-brand" />
          Report without an account
        </Link>
      }
    >
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3">
        <FormField
          label="Username or email"
          autoComplete="username"
          error={form.formState.errors.username?.message}
          {...form.register('username')}
        />
        <FormField
          label="Password"
          type="password"
          autoComplete="current-password"
          error={form.formState.errors.password?.message}
          {...form.register('password')}
        />
        <Link to="/forgot" className="self-end text-[13px] font-bold text-brand">
          Forgot password?
        </Link>
        <Btn type="submit" loading={form.formState.isSubmitting} className="mt-2">
          Sign in
        </Btn>
      </form>
      <p className="mt-5 text-center text-sm text-ink-2">
        New here?{' '}
        <Link to="/register" className="font-bold text-brand">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  )
}
