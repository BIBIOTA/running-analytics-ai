import { test, expect } from '@playwright/test';

test('authenticated user lands on a protected page after navigating to /', async ({ page }) => {
  await page.goto('/');

  // Should not be redirected to /login
  await expect(page).not.toHaveURL(/\/login/);
});

test('authenticated page renders the user display name from /auth/me', async ({ page }) => {
  await page.goto('/');

  // The page must render some user-identifying text.
  // Replace STRAVA_TEST_DISPLAY_NAME in .env.e2e with the display name of your test account.
  const displayName = process.env.STRAVA_TEST_DISPLAY_NAME;
  if (!displayName) {
    test.skip(true, 'Set STRAVA_TEST_DISPLAY_NAME in .env.e2e to enable this assertion');
  }
  await expect(page.getByText(displayName!)).toBeVisible();
});
