import { expect, test } from '@playwright/test'
import { installApiMock, user } from './api-mock'

test('a signed-in user captures a photo, sets location, and submits a report', async ({ page }) => {
  const state = await installApiMock(page, { authed: user() })
  await page.goto('/report')

  // 1. Open the in-app camera (no upload option) and shoot - Chromium's fake device supplies
  //    a video stream so getUserMedia + canvas capture work headless.
  await page.getByText(/tap to capture the pollution/i).click()
  const shutter = page.getByRole('button', { name: /take photo/i })
  await expect(shutter).toBeVisible()
  await shutter.click({ force: true })

  // Back on the form, the captured photo shows a "Retake" affordance.
  await expect(page.getByText(/retake/i)).toBeVisible()

  // 2. Set the location via GPS (geolocation is granted + stubbed in the config).
  await page.getByRole('button', { name: /use my location/i }).click()

  // 3. Submit.
  await page.getByRole('button', { name: /submit report/i }).click()

  // Success navigates back to the home feed, and the app POSTed exactly one report with the
  // captured photo + chosen severity. (Chromium's fake camera doesn't render real frames
  // headless, so we assert the flow and payload, not the pixels.)
  await expect(page.getByRole('heading', { name: /recent reports/i })).toBeVisible()
  expect(state.submitted).toHaveLength(1)
  expect(state.submitted[0]).toMatchObject({ severity: 3 })
  expect(state.submitted[0].photo).toBeTruthy()
})
