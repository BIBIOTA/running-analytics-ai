import { test as setup } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const AUTH_FILE = path.resolve(__dirname, '.auth/user.json');

setup('authenticate via Strava', async ({ page }) => {
  const email = process.env.STRAVA_TEST_EMAIL;
  const password = process.env.STRAVA_TEST_PASSWORD;

  if (!email || !password) {
    throw new Error(
      'Missing STRAVA_TEST_EMAIL or STRAVA_TEST_PASSWORD in tests/e2e/.env.e2e'
    );
  }

  // Ensure .auth/ directory exists
  fs.mkdirSync(path.dirname(AUTH_FILE), { recursive: true });

  // Navigate to login page and click the Strava OAuth button
  await page.goto('/login');
  await page.getByRole('link', { name: /continue with strava/i }).click();

  // Now on Strava's OAuth page. Strava may show a login form if not already logged in.
  // Wait for either the login form or the authorize button.
  await page.waitForURL(/strava\.com/);

  const emailInput = page.getByLabel(/email/i);
  const isLoginForm = await emailInput.isVisible().catch(() => false);

  if (isLoginForm) {
    await emailInput.fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole('button', { name: /log in/i }).click();
  }

  // After login, Strava shows the Authorize page. Click Authorize.
  await page.getByRole('button', { name: /authorize/i }).click();

  // Wait for the frontend callback to process the token and navigate away from /callback
  await page.waitForURL((url) => !url.pathname.startsWith('/callback'), {
    timeout: 30_000,
  });

  // Save authenticated browser state
  await page.context().storageState({ path: AUTH_FILE });
});
