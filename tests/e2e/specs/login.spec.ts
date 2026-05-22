import { test, expect } from '@playwright/test';

// Override: these tests run without stored session
test.use({ storageState: { cookies: [], origins: [] } });

test('login page shows Continue with Strava button', async ({ page }) => {
  await page.goto('/login');

  await expect(
    page.getByRole('link', { name: /continue with strava/i })
  ).toBeVisible();
});

test('clicking Strava button redirects to strava.com OAuth with correct params', async ({ page }) => {
  await page.goto('/login');

  // waitForURL captures the final URL after the redirect chain:
  // /api/auth/strava (Vite proxy) → backend 302 → strava.com/oauth/authorize
  await Promise.all([
    page.waitForURL(/strava\.com\/oauth\/authorize/),
    page.getByRole('link', { name: /continue with strava/i }).click(),
  ]);

  const url = new URL(page.url());
  expect(url.hostname).toBe('www.strava.com');
  expect(url.pathname).toBe('/oauth/authorize');
  expect(url.searchParams.get('response_type')).toBe('code');
  expect(url.searchParams.get('scope')).toContain('activity:read_all');
  expect(url.searchParams.get('client_id')).toBeTruthy();
});

test('unauthenticated access to /dashboard redirects to /login', async ({ page }) => {
  await page.goto('/dashboard');

  await expect(page).toHaveURL(/\/login/);
});
