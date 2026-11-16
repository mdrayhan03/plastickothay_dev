import { useEffect, useRef } from 'react'
import { useNavigate, useLocation, useParams, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'
import type { OAuthProvider } from '@/services/oauthProviderService'
import { apiErrorMessage } from '@/lib/api'
import { toast } from 'sonner'

export function OAuthCallbackPage() {
  const { provider } = useParams<{ provider: OAuthProvider }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string })?.from ?? '/'
  const hasExchanged = useRef(false)
  const { loginWithOAuth } = useAuth()

  useEffect(() => {
    // Prevent duplicate request in React 18 StrictMode (auth codes are single-use)
    if (hasExchanged.current) return
    hasExchanged.current = true

    const code = searchParams.get('code')
    const oauthError = searchParams.get('error')

    if (oauthError) {
      toast.error(`Authorization cancelled or failed: ${oauthError}`)
      navigate('/login', {replace: true})
    }

    if (!provider || !code) {
      toast.error('Missing OAuth provider or authorization code.')
      navigate('/login', {replace: true})
    }

    const redirectUri = `${window.location.origin}/auth/callback/${provider!}`

    try {
        loginWithOAuth(provider!, code!, redirectUri)
        navigate(from, {replace: true})
    } catch (err) {
        toast.error(apiErrorMessage(err, "Authentication failed. Please try again."))
        navigate('/login', {replace: true})
    }
  }, [provider, searchParams, navigate])

  return <p>Completing sign in...</p>
}