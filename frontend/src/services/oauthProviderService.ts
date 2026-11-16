export type OAuthProvider = 'google' | 'github' | 'facebook'

export interface OAuthProviderConfig {
  id: OAuthProvider
  label: string
}

export const OAUTH_PROVIDERS: OAuthProviderConfig[] = [
  { id: 'google', label: 'Continue with Google' },
  // { id: 'github', label: 'Continue with GitHub' },
  // { id: 'facebook', label: 'Continue with Facebook' },
]

export const oauthProviderService = {
  getRedirectUri(provider: OAuthProvider): string {
    return `${window.location.origin}/auth/callback/${provider}`
  },

  buildAuthorizeUrl(provider: OAuthProvider): string {
    const redirectUri = this.getRedirectUri(provider)
    

    switch (provider) {
      case 'google': {
        const params = new URLSearchParams({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
          redirect_uri: redirectUri,
          response_type: 'code',
          scope: 'openid email profile',
          access_type: 'offline',
          prompt: 'select_account',
        })
        console.log(params.toString());
        return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`
      }

      case 'github': {
        const params = new URLSearchParams({
          client_id: import.meta.env.VITE_GITHUB_CLIENT_ID,
          redirect_uri: redirectUri,
          scope: 'read:user user:email',
        })
        return `https://github.com/login/oauth/authorize?${params.toString()}`
      }

      case 'facebook': {
        const params = new URLSearchParams({
          client_id: import.meta.env.VITE_FACEBOOK_APP_ID,
          redirect_uri: redirectUri,
          response_type: 'code',
          scope: 'email,public_profile',
        })
        return `https://www.facebook.com/v19.0/dialog/oauth?${params.toString()}`
      }
    }
  },

  startLogin(provider: OAuthProvider): void {
    window.location.href = this.buildAuthorizeUrl(provider)
  },
}