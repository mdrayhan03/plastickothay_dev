import { expect, test } from '@playwright/test'
import { installApiMock, user } from './api-mock'

test('a user can sign in and see their profile', async ({ page }) => {
  await installApiMock(page, { authed: null }) // anonymous on boot; login sets the session
  await page.goto('/login')

  await page.getByRole('textbox').first().fill('rahim')
  await page.locator('input[type="password"]').fill('s3cretpass')
  await page.getByRole('button', { name: /sign in/i }).click()

  // Signed in: the home header greets the user by first name (anon shows a plain "Welcome").
  await expect(page.getByText(new RegExp(`welcome, ${user().first_name}`, 'i'))).toBeVisible()
  // ...and the More tab now offers Log out instead of Sign in.
  await page.getByRole('link', { name: /more/i }).click()
  await expect(page.getByRole('button', { name: /log out/i })).toBeVisible()
})

test('protected route redirects an anonymous user to login', async ({ page }) => {
  await installApiMock(page, { authed: null })
  await page.goto('/me')
  await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
})
