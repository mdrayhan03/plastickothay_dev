import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Dev-only: where `npm run dev` proxies /api. Configurable so the backend can run on any
  // host/port without editing this file. Defaults to the local Django dev server.
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const backend = env.VITE_BACKEND_URL || 'http://localhost:8000'
  const port = Number(env.VITE_PORT) || 5173

  return {
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      workbox: {
        // SPA deep-links resolve to the cached shell when offline; never for the API/admin.
        navigateFallback: 'index.html',
        navigateFallbackDenylist: [/^\/api/, /^\/django-admin/],
        runtimeCaching: [
          {
            // Map tiles - cache-first so a previously-viewed map still renders offline.
            urlPattern: /^https:\/\/[a-d]\.basemaps\.cartocdn\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 14 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Public GET data - network-first, falling back to the last response offline.
            urlPattern: ({ url, request }: { url: URL; request: Request }) =>
              url.pathname.startsWith('/api/') && request.method === 'GET',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-get',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      manifest: {
        name: 'PlasticKothay',
        short_name: 'PlasticKothay',
        description: 'Map plastic pollution. Clean up your city, together.',
        theme_color: '#0A9C74',
        background_color: '#EEF4F0',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
    }),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    // Dev port from VITE_PORT (default 5173); strict so a conflict fails loudly instead of
    // silently hopping to another port and breaking the proxy assumption.
    port,
    strictPort: true,
    // Same-origin in dev: the browser sees /api as first-party, so the httpOnly
    // refresh cookie works and there is no CORS. Prod serves the build from Django.
    proxy: {
      '/api': { target: backend, changeOrigin: true },
    },
  },
  }
})
