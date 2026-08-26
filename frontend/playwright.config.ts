import { defineConfig, devices } from '@playwright/test'
import { loadEnv } from 'vite'

// Match the dev server's port (VITE_PORT in .env, default 5173) so the mocked e2e run and the
// webServer agree even when the port is changed to dodge a conflict.
const viteEnv = loadEnv('development', process.cwd(), 'VITE_')
const PORT = Number(process.env.VITE_PORT || viteEnv.VITE_PORT) || 5173
const BASE_URL = process.env.E2E_BASE_URL || `http://localhost:${PORT}`

/**
 * E2E runs the built app in a real browser with the API mocked (see e2e/api-mock.ts), so it's
 * deterministic and needs no backend or DB. Point it at a live stack with E2E_BASE_URL to run
 * the same specs against a real server (the mocks are opt-in per test).
 *
 * Chromium gets a fake camera device so the in-app getUserMedia capture works headless.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  // One retry absorbs transient cold-start slowness (Vite compiles routes on first hit under
  // parallel workers); a real failure still fails on the retry.
  retries: process.env.CI ? 2 : 1,
  reporter: process.env.CI ? 'line' : [['list']],
  use: {
    baseURL: BASE_URL,
    // The user portal is mobile-first; default the specs to a phone viewport (bottom nav,
    // single column). Desktop-first flows (admin) override this per-file with test.use().
    viewport: { width: 390, height: 844 },
    permissions: ['camera', 'geolocation'],
    geolocation: { latitude: 23.78, longitude: 90.4 },
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'],
        },
      },
    },
  ],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: 'npm run dev',
        port: PORT,
        reuseExistingServer: !process.env.CI,
        timeout: 60_000,
      },
})
