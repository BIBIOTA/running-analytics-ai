# E2E Integration Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up a Playwright E2E suite under `tests/e2e/` that runs complete user journeys (login → authenticated pages) against locally running Docker Compose services using real Strava OAuth credentials.

**Architecture:** A standalone TypeScript package under `tests/e2e/` contains a `global-setup.ts` that performs one real Strava OAuth login and persists browser storage state to `.auth/user.json`. All authenticated specs load that state, skipping repeated logins. Unauthenticated specs (login page) clear the state explicitly at the test level.

**Tech Stack:** `@playwright/test` 1.x, TypeScript, `dotenv`, Chromium browser.

---

## Prerequisites (must be true before running any test)

1. `make dev` (or `docker compose up`) is running — backend at `http://localhost:8000`, frontend at `http://localhost:3000`.
2. The frontend has routing: a `/login` route rendering the Strava login button, and a `/callback` route that reads `?token=` from the URL, stores the JWT in `localStorage`, then navigates to the authenticated area.
3. A real Strava test account exists whose credentials you can put in `.env.e2e`.
4. The Strava developer app has `http://localhost:8000` listed as an authorized callback domain in the Strava API settings.

---

## File Map

| Action | Path |
|--------|------|
| Create | `tests/e2e/package.json` |
| Create | `tests/e2e/tsconfig.json` |
| Create | `tests/e2e/playwright.config.ts` |
| Create | `tests/e2e/.env.e2e.example` |
| Create | `tests/e2e/global-setup.ts` |
| Create | `tests/e2e/specs/login.spec.ts` |
| Create | `tests/e2e/specs/dashboard.spec.ts` |
| Modify | `Makefile` |
| Modify | `.gitignore` |

---

## Task 1: Scaffold the `tests/e2e/` package

**Files:**
- Create: `tests/e2e/package.json`
- Create: `tests/e2e/tsconfig.json`

- [ ] **Step 1: Create `tests/e2e/package.json`**

```json
{
  "name": "@running-analytics-ai/e2e",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "test": "playwright test",
    "test:ui": "playwright test --ui"
  },
  "devDependencies": {
    "@playwright/test": "^1.44.0",
    "dotenv": "^16.4.0"
  },
  "engines": {
    "node": ">=20"
  }
}
```

- [ ] **Step 2: Create `tests/e2e/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "outDir": "./dist",
    "baseUrl": "."
  },
  "include": ["./**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

- [ ] **Step 3: Install dependencies**

```bash
cd tests/e2e && npm install
```

Expected: `node_modules/@playwright/test` directory created.

- [ ] **Step 4: Commit scaffold**

```bash
git add tests/e2e/package.json tests/e2e/tsconfig.json tests/e2e/package-lock.json
git commit -m "chore(e2e): scaffold Playwright package"
```

---

## Task 2: Write `playwright.config.ts`

**Files:**
- Create: `tests/e2e/playwright.config.ts`

- [ ] **Step 1: Create the config**

```typescript
import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '.env.e2e') });

export default defineConfig({
  testDir: './specs',
  timeout: 60_000,
  retries: 0,
  workers: 1,
  reporter: [['list']],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'setup',
      testMatch: /global-setup\.ts/,
    },
    {
      name: 'e2e',
      testMatch: /specs\/.*\.spec\.ts/,
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/user.json',
      },
    },
  ],
});
```

- [ ] **Step 2: Commit**

```bash
git add tests/e2e/playwright.config.ts
git commit -m "chore(e2e): add Playwright config"
```

---

## Task 3: Add `.env.e2e.example` and update `.gitignore`

**Files:**
- Create: `tests/e2e/.env.e2e.example`
- Modify: `.gitignore`

- [ ] **Step 1: Create `.env.e2e.example`**

```bash
# Copy to .env.e2e and fill in your Strava test account credentials.
# This file is committed. .env.e2e is gitignored.
STRAVA_TEST_EMAIL=your-strava-test-account@example.com
STRAVA_TEST_PASSWORD=your-strava-password
```

- [ ] **Step 2: Add entries to root `.gitignore`**

Open `.gitignore` and append these three lines at the end:

```
tests/e2e/.auth/
tests/e2e/.env.e2e
tests/e2e/node_modules/
```

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/.env.e2e.example .gitignore
git commit -m "chore(e2e): add env example and gitignore entries"
```

---

## Task 4: Write `global-setup.ts`

This file is matched by the `setup` project in `playwright.config.ts`. It runs once before all specs, performs a real Strava OAuth login, and saves the authenticated browser state to `.auth/user.json`.

**Files:**
- Create: `tests/e2e/global-setup.ts`

- [ ] **Step 1: Create `tests/e2e/global-setup.ts`**

```typescript
import { test as setup, expect } from '@playwright/test';
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
```

- [ ] **Step 2: Verify the file is syntactically valid**

```bash
cd tests/e2e && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/global-setup.ts
git commit -m "feat(e2e): add global-setup for Strava OAuth login"
```

---

## Task 5: Write `specs/login.spec.ts`

Tests the unauthenticated login page. These tests clear storageState so they run without a session even though the `e2e` project provides one.

**Files:**
- Create: `tests/e2e/specs/login.spec.ts`

- [ ] **Step 1: Create `tests/e2e/specs/login.spec.ts`**

```typescript
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
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd tests/e2e && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/specs/login.spec.ts
git commit -m "feat(e2e): add login page spec"
```

---

## Task 6: Write `specs/dashboard.spec.ts`

Tests authenticated state. Uses the storageState saved by `global-setup.ts`. Verifies the user reaches an authenticated page and their display name is rendered.

**Files:**
- Create: `tests/e2e/specs/dashboard.spec.ts`

- [ ] **Step 1: Create `tests/e2e/specs/dashboard.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';

test('authenticated user lands on a protected page after navigating to /', async ({ page }) => {
  await page.goto('/');

  // Should not be redirected to /login
  await expect(page).not.toHaveURL(/\/login/);
});

test('authenticated page renders the user display name from /auth/me', async ({ page }) => {
  await page.goto('/');

  // The page must render some user-identifying text.
  // This test will need updating once the authenticated layout is built —
  // replace 'your-strava-display-name' with the display name of your test account.
  const displayName = process.env.STRAVA_TEST_DISPLAY_NAME;
  if (!displayName) {
    test.skip(true, 'Set STRAVA_TEST_DISPLAY_NAME in .env.e2e to enable this assertion');
  }
  await expect(page.getByText(displayName!)).toBeVisible();
});
```

- [ ] **Step 2: Add `STRAVA_TEST_DISPLAY_NAME` to `.env.e2e.example`**

Open `tests/e2e/.env.e2e.example` and append:

```bash
# Display name shown by the app after login (e.g. "Ada Runner").
# Used to verify the authenticated UI renders user data.
STRAVA_TEST_DISPLAY_NAME=Ada Runner
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd tests/e2e && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/specs/dashboard.spec.ts tests/e2e/.env.e2e.example
git commit -m "feat(e2e): add authenticated dashboard spec"
```

---

## Task 7: Add Makefile targets and install Chromium

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Install Playwright's Chromium browser**

```bash
cd tests/e2e && npx playwright install chromium --with-deps
```

Expected: Chromium downloaded to Playwright's cache directory.

- [ ] **Step 2: Add targets to `Makefile`**

Open `Makefile`. Change the first line and add two new targets so the final file reads:

```makefile
.PHONY: dev lint test generate-api test-e2e test-e2e-ui

dev:
	docker compose up

lint:
	cd apps/backend && ruff check app tests && ruff format --check app tests && mypy app
	@if [ -f apps/frontend/package.json ]; then cd apps/frontend && npm run lint; fi

test:
	cd apps/backend && pytest

generate-api:
	curl -fsS http://localhost:8000/openapi.json -o api-contract/openapi.json
	@if [ -f apps/frontend/package.json ]; then cd apps/frontend && npm run generate-api; fi

test-e2e:
	cd tests/e2e && npm install --silent && npx playwright install chromium --with-deps && npx playwright test

test-e2e-ui:
	cd tests/e2e && npx playwright test --ui
```

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore(e2e): add test-e2e and test-e2e-ui Makefile targets"
```

---

## Task 8: Smoke-test the full setup

This task verifies everything wires together correctly. It requires Docker Compose services to be running and `.env.e2e` to be populated.

- [ ] **Step 1: Confirm services are up**

```bash
curl -sf http://localhost:8000/health && echo "backend OK"
curl -sf http://localhost:3000 && echo "frontend OK"
```

Expected: both print their respective OK message.

- [ ] **Step 2: Create `.env.e2e` with real credentials**

```bash
cp tests/e2e/.env.e2e.example tests/e2e/.env.e2e
# Edit tests/e2e/.env.e2e — fill in STRAVA_TEST_EMAIL, STRAVA_TEST_PASSWORD, STRAVA_TEST_DISPLAY_NAME
```

- [ ] **Step 3: Run the full suite**

```bash
make test-e2e
```

Expected output (when frontend routing and callback page are implemented):
- `setup > authenticate via Strava` — PASSED
- `e2e > login page shows Continue with Strava button` — PASSED
- `e2e > clicking Strava button redirects to strava.com...` — PASSED
- `e2e > authenticated user lands on a protected page` — PASSED
- `e2e > authenticated page renders the user display name` — PASSED (if `STRAVA_TEST_DISPLAY_NAME` is set)

If the frontend `/callback` route is not yet implemented, `global-setup.ts` will time out at the `waitForURL` step. Implement the `/callback` route first (store JWT from `?token=` in localStorage, then `navigate('/')`) before running the full suite.

- [ ] **Step 4: Verify `.auth/user.json` is not tracked by git**

```bash
git status tests/e2e/.auth/
```

Expected: no output (directory is gitignored).

---

## Appendix: How storageState interacts with JWT auth

The frontend stores the JWT in `localStorage` after the `/callback` route processes `?token=`. Playwright's `storageState` captures `localStorage` per origin, so the saved `.auth/user.json` contains the JWT. When authenticated specs load this state, the frontend's `apiClient` reads the token from `localStorage` on each request and sends it as `Authorization: Bearer <token>`.

If the JWT expires (typically hours), re-run `make test-e2e` — `global-setup.ts` always executes first and refreshes `.auth/user.json`.
