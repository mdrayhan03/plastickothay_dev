import { expect, test } from '@playwright/test'
import { installApiMock, user } from './api-mock'

const staff = user({ role: 'staff', first_name: 'Mod', last_name: 'Erator' })

test('staff can open the review queue and approve a pending report', async ({ page }) => {
  await installApiMock(page, { authed: staff })
  await page.goto('/admin/review')

  await expect(page.getByRole('heading', { name: /review queue/i })).toBeVisible()
  await expect(page.getByText('#201')).toBeVisible()
  await expect(page.getByText('#202')).toBeVisible()

  // Approve the first pending report; the queue refetches and drops it.
  await page.getByTitle('Approve').first().click()
  await expect(page.getByText('#201')).toHaveCount(0)
  await expect(page.getByText('#202')).toBeVisible()
})

test('a normal user cannot reach the admin portal', async ({ page }) => {
  await installApiMock(page, { authed: user({ role: 'user' }) })
  await page.goto('/admin/review')
  // StaffRoute bounces non-staff to the user home.
  await expect(page.getByRole('heading', { name: /recent reports/i })).toBeVisible()
})
