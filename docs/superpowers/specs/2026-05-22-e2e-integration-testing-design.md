# E2E Integration Testing Design

**Date:** 2026-05-22  
**Scope:** Full-stack browser-based E2E tests covering all current UI pages, running locally against `docker compose up` services with real Strava OAuth.

---

## Goal

Verify complete user journeys from browser UI through the frontend, backend API, and MongoDB — catching regressions that unit tests (which mock at the HTTP or DB boundary) cannot catch.

---

## Constraints

- Local development only (not CI/CD)
- Uses real Strava credentials for OAuth (a dedicated test account)
- Requires `docker compose up` services to be running before test execution
- Accepts the inherent fragility of automating a third-party OAuth UI

---

## Directory Structure

```
running-analytics-ai/
├── tests/
│   └── e2e/
│       ├── package.json          # @playwright/test, dotenv
│       ├── playwright.config.ts  # baseURL, projects, globalSetup
│       ├── .env.e2e.example      # STRAVA_TEST_EMAIL, STRAVA_TEST_PASSWORD
│       ├── .env.e2e              # gitignored — real test account credentials
│       ├── .auth/                # gitignored — storageState JSON
│       ├── global-setup.ts       # one-time real Strava login → saves .auth/user.json
│       └── specs/
│           ├── login.spec.ts     # unauthenticated state tests
│           └── dashboard.spec.ts # authenticated state tests
├── Makefile                      # test-e2e and test-e2e-ui targets added
└── .gitignore                    # tests/e2e/.auth/, tests/e2e/.env.e2e added
```

---

## Tooling

| Tool | Purpose |
|------|---------|
| `@playwright/test` | Test runner + browser automation |
| TypeScript | Consistent with frontend |
| `dotenv` | Load `.env.e2e` credentials in global setup |
| Chromium | Single browser target (local dev) |

No test database is introduced — tests run against the real MongoDB started by `docker compose up`.

---

## Auth Setup Flow

`global-setup.ts` executes once before all specs:

1. Open browser with no storageState
2. Navigate to `http://localhost:3000/login`
3. Click "Continue with Strava" → redirect to `https://www.strava.com/oauth/authorize?...`
4. Fill `STRAVA_TEST_EMAIL` and `STRAVA_TEST_PASSWORD` using role-based selectors (`page.getByLabel('Email')`)
5. Click Strava's Authorize button → callback redirects to `http://localhost:3000/callback?token=...`
6. Wait for frontend to complete JWT storage and navigate to authenticated route
7. Save `context.storageState()` to `.auth/user.json`
8. Close browser

Subsequent test runs re-execute `global-setup.ts`, refreshing the stored state. JWT expiry is not a problem because setup always runs first.

**Strava selector fragility:** Strava's login DOM can change. Role-based selectors (`getByLabel`, `getByRole`) are more resilient than CSS class selectors, but this is an accepted risk of real third-party OAuth E2E.

---

## Playwright Config

Two projects defined:

```ts
projects: [
  {
    name: 'setup',
    testMatch: /global-setup\.ts/,
  },
  {
    name: 'authenticated',
    testMatch: /specs\/.*\.spec\.ts/,
    dependencies: ['setup'],
    use: { storageState: '.auth/user.json' },
  },
]
```

---

## Test Specs

### `specs/login.spec.ts` — unauthenticated

- Navigating to `/login` shows "Continue with Strava" button
- Clicking the button redirects to `strava.com` with correct `client_id` and `scope` in query params
- Navigating to `/dashboard` without auth redirects to `/login`

### `specs/dashboard.spec.ts` — authenticated (uses storageState)

- Navigating to `/` redirects to the main authenticated route
- Page displays the authenticated user's `display_name`

Note: API correctness is verified indirectly — if the page renders user data, `/auth/me` returned 200 with valid shape. Direct `page.request` calls to the backend require manually extracting the JWT from `localStorage` first (Bearer token auth, not cookies), so prefer UI assertions over raw API assertions in authenticated specs.

---

## Test Conventions

- Each spec tests one user journey; no shared mutable state between specs
- Prefer `page.getByRole()` / `page.getByText()` / `page.getByLabel()` over CSS selectors
- API assertions use `page.request` directly against `http://localhost:8000`, not through the browser proxy
- New pages added to the app get a corresponding spec file

---

## Makefile Targets

```makefile
test-e2e:
	cd tests/e2e && npm install --silent && npx playwright install chromium --with-deps && npx playwright test

test-e2e-ui:
	cd tests/e2e && npx playwright test --ui
```

---

## Setup Instructions

```bash
# 1. Start services
make dev

# 2. Create credentials file
cp tests/e2e/.env.e2e.example tests/e2e/.env.e2e
# Edit .env.e2e: fill in STRAVA_TEST_EMAIL and STRAVA_TEST_PASSWORD

# 3. Run E2E tests
make test-e2e

# 4. (Optional) Interactive debug UI
make test-e2e-ui
```

---

## .gitignore Additions

```
tests/e2e/.auth/
tests/e2e/.env.e2e
tests/e2e/node_modules/
```
