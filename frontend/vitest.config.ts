import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Separate from vite.config so tests don't run the PWA plugin.
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    // Unit/component tests live in src/; e2e/ is Playwright's (different runner).
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})
