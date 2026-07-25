import { expect, test } from '@playwright/test'
import { installApiMock } from './api-mock'

test('public home renders the map header and the report feed', async ({ page }) => {
  await installApiMock(page, { authed: null })
  await page.goto('/')

  // Header pulls the city from site-config; the feed lists approved reports.
  await expect(page.getByRole('heading', { name: /recent reports/i })).toBeVisible()
  await expect(page.getByText('Hatirjheel, Dhaka')).toBeVisible()
  await expect(page.getByText('Buriganga bank')).toBeVisible()
})

test('tapping a feed card opens the report detail sheet', async ({ page }) => {
  await installApiMock(page, { authed: null })
  await page.goto('/')

  await page.getByText('Hatirjheel, Dhaka').first().click()
  const sheet = page.getByRole('dialog', { name: /report details/i })
  await expect(sheet).toBeVisible()
  await expect(sheet.getByText(/plastic pile near the canal/i)).toBeVisible()
})
