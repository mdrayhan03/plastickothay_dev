import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from '@/App'
import { PhoneFrame } from '@/components/layout/PhoneFrame'
import { AuthProvider } from '@/context/AuthContext'
import { queryClient } from '@/lib/queryClient'
// Self-hosted fonts (bundled — no CDN, works offline/PWA)
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/plus-jakarta-sans'
import '@fontsource/hind-siliguri/500.css'
import '@fontsource/hind-siliguri/700.css'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <PhoneFrame>
            <App />
          </PhoneFrame>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
