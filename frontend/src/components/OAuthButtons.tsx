// src/components/auth/OAuthButtons.tsx
import type { JSX } from 'react'
import {
  OAUTH_PROVIDERS,
  oauthProviderService,
  type OAuthProvider,
} from '@/services/oauthProviderService'

const PROVIDER_ICONS: Record<OAuthProvider, JSX.Element> = {
  google: (
    <svg className="size-5" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 5c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 1.77 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.91 6.16-4.91z"
      />
      <path
        fill="#4285F4"
        d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47c-.29 1.48-1.14 2.73-2.4 3.58v3h3.86c2.26-2.09 3.56-5.17 3.56-8.82z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
      />
      <path
        fill="#34A853"
        d="M12 23c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.16-4.07 1.16-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
    </svg>
  ),
  github: (
    <svg className="size-5 fill-white" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 1.5C6.2 1.5 1.5 6.2 1.5 12c0 4.64 3.01 8.57 7.18 9.96.53.1.72-.23.72-.51 0-.25-.01-.92-.01-1.8-2.92.63-3.54-1.41-3.54-1.41-.48-1.21-1.17-1.54-1.17-1.54-.95-.65.07-.64.07-.64 1.05.07 1.61 1.08 1.61 1.08.94 1.6 2.46 1.14 3.06.87.09-.68.37-1.14.67-1.4-2.33-.26-4.78-1.17-4.78-5.19 0-1.15.41-2.08 1.08-2.82-.11-.26-.47-1.33.1-2.78 0 0 .88-.28 2.89 1.08a10.04 10.04 0 0 1 5.26 0c2.01-1.36 2.89-1.08 2.89-1.08.57 1.45.21 2.52.1 2.78.67.74 1.08 1.67 1.08 2.82 0 4.03-2.46 4.92-4.8 5.18.38.33.71.97.71 1.96 0 1.41-.01 2.55-.01 2.9 0 .28.19.61.73.51A10.503 10.503 0 0 0 22.5 12c0-5.8-4.7-10.5-10.5-10.5z"
      />
    </svg>
  ),
  facebook: (
    <svg className="size-5" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#1877F2"
        d="M24 12.07C24 5.41 18.63 0 12 0S0 5.41 0 12.07c0 6.02 4.39 11.01 10.13 11.93v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.97h-1.51c-1.49 0-1.95.93-1.95 1.88v2.26h3.33l-.53 3.49h-2.8V24C19.61 23.08 24 18.09 24 12.07z"
      />
    </svg>
  ),
}

interface OAuthButtonsProps {
  disabled?: boolean
}

export function OAuthButtons({ disabled = false }: OAuthButtonsProps) {
  return (
    <div className="mt-5 w-full space-y-4">
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-emerald-900/60" />
        <span className="text-xs font-medium text-neutral-400">
          Or continue with
        </span>
        <div className="h-px flex-1 bg-emerald-900/60" />
      </div>

      <div className="flex gap-3">
        {OAUTH_PROVIDERS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            disabled={disabled}
            aria-label={label}
            title={label}
            onClick={() => oauthProviderService.startLogin(id)}
            className="flex h-12 w-full cursor-pointer items-center justify-center rounded-xl border border-emerald-900/70 bg-emerald-950/40 transition-all duration-150 hover:border-emerald-500/60 hover:bg-emerald-900/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {PROVIDER_ICONS[id]}
          </button>
        ))}
      </div>
    </div>
  )
}