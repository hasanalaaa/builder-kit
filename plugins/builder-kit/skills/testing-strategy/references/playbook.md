# Testing playbook

## 1. Levels and what they prove

| Level | Proves | Speed | Share (typical web app) |
|-------|--------|-------|-------------------------|
| Static (types, lint, schema validation) | whole classes of bugs never compile | instant | always on |
| Unit | pure logic: pricing, permissions rules, parsers, formatters, reducers | ms | many |
| Integration | a handler/use case with real DB, auth, validation, serialization | 10–500ms | most value per test |
| Component | UI renders states and responds to user events (Testing Library) | 10–100ms | for interactive components |
| Contract | API shape matches what clients expect (OpenAPI/schema/Pact) | fast | public/mobile APIs |
| E2E | a real user journey through the deployed stack in a browser/device | seconds | few, critical journeys |
| Visual regression | UI didn't change unexpectedly (Playwright screenshots, Chromatic) | seconds | design-system components, key pages |
| Accessibility | axe rules pass, keyboard flow works | fast | every page in E2E |
| Load / perf | p95 latency and error rate under expected load (k6) | minutes | before launch, big changes |
| Security abuse | 401/403/404/400/429, injection, IDOR | fast | every protected endpoint (launch-security 27) |

Shape: "testing trophy" for web apps (most weight on integration), pyramid for libraries (most on unit).

## 2. What to test where

- **Business rules** (prices, discounts, eligibility, state transitions): unit, table-driven.
- **Endpoints / server actions**: integration through the HTTP layer or the action function with a real test DB: success, each error status, ownership, validation, idempotency.
- **Database**: constraints reject bad data, RLS policies (Supabase: run as `anon` and as two different users), migrations apply on a copy.
- **UI components**: render each state (loading/empty/error/success), user events by role/label (`getByRole('button', { name: 'Save' })`), RTL rendering for directional components.
- **Journeys** (E2E): sign up → first value; checkout/payment (test mode); critical admin action; password reset. Run against preview deployments.
- **Mobile**: unit + component (React Native Testing Library / XCTest / Compose tests) + a few E2E (Maestro / Detox / XCUITest).

## 3. Tools by stack

| Stack | Unit/integration | Component | E2E | Mocks |
|-------|------------------|-----------|-----|-------|
| TS / Next.js / Vite | Vitest (or Jest) | Testing Library + jsdom/happy-dom | Playwright | MSW for HTTP; testcontainers or Supabase local for DB |
| Node API | Vitest + supertest / Hono `app.request` | — | Playwright API | MSW, nock |
| Python / FastAPI / Django | pytest + httpx `AsyncClient` / Django test client | — | Playwright (python) | respx, responses; pytest-postgresql/testcontainers |
| Expo / React Native | Jest + RNTL | RNTL | Maestro / Detox | MSW (native) |
| SwiftUI | Swift Testing / XCTest | ViewInspector / snapshot | XCUITest | URLProtocol stubs |
| Android | JUnit + Robolectric | Compose UI test | Espresso / Maestro | MockWebServer |
| Load | k6 | | | |
| Accessibility | jest-axe / vitest-axe | | @axe-core/playwright | |

## 4. From acceptance criteria to tests

```
Given a staff member not assigned to C's class, when they post for C, then 403 and nothing saved.
→ test("staff outside class cannot post update", async () => {
    const res = await api.as(staffB).post(`/children/${childC}/updates`, validUpdate);
    expect(res.status).toBe(403);
    expect(await db.updates.count({ childId: childC })).toBe(0);
  });
```
Name tests as behavior sentences. One behavior per test. Arrange–Act–Assert.

## 5. Data: fixtures and factories

- Factories create valid objects with overrides: `makeUser({ role: 'admin' })` (fishery, @faker-js/faker, factory_boy).
- Each test creates its own data; never depend on order or on shared seed rows being unchanged.
- Isolation: transaction rollback per test, or truncate between tests, or a unique tenant per test.
- No real personal data in fixtures; fake but realistic (Arabic names, long strings, emoji, RTL text).
- Time: fake timers / freezegun; randomness: seeded.

## 6. Mocking rules

- Mock at the network boundary (MSW/respx), not inside your own modules.
- Never call real third parties in tests (Stripe, OpenAI, email). Use their test modes only in dedicated E2E/staging runs.
- Contract-check mocks: keep recorded responses close to the provider's real schema; update when the provider changes.
- Don't mock the database in integration tests; use a real one (container or local Supabase).

## 7. E2E rules (Playwright)

- Select by role, label, text, or `data-testid` (stable), never CSS classes.
- Auto-waiting assertions (`await expect(locator).toBeVisible()`), never `waitForTimeout`.
- Authenticate once per worker via storage state; create test users via API, not UI.
- Run in CI against the preview URL; trace + video on failure.
- Also run: mobile viewport, `locale: 'ar'` with RTL, dark mode for key pages; axe scan on each page.
- Keep the suite small: critical journeys only (5–20 tests for most apps).

## 8. Flakiness

Causes: timing (sleeps, animations), shared data, order dependence, real network, time zones, randomness, resource limits.
Process: retry once in CI to unblock, tag the test as flaky, open an issue, fix root cause within the sprint, never "retry forever".

## 9. CI gates

1. Lint + format check + typecheck.
2. Unit + integration (parallel), with coverage report.
3. Build.
4. E2E against the preview deployment.
5. Security and structure scans: `security_scan.py`, `arch_check.py`, `error_scan.py`, `design_lint.py` (builder-kit `ship-check` runs them together).
Merge blocked on red. Main branch always green.

## 10. Coverage targets

- Critical paths (auth, permissions, payments, data writes, pricing): ≥ 90% lines + branch, and mutation testing (Stryker / mutmut) for the money logic.
- Rest of the app: whatever the behavior tests give; don't chase 100%.
- New code in a PR shouldn't lower coverage of critical modules.

## 11. AI-specific rules

- When an AI agent changes code, it runs the tests and reports the actual output; "should pass" is not a result.
- Agents may not delete, skip, or loosen assertions to get green. A test change needs a stated reason (spec changed / test was wrong).
- Ask the agent to write the test first and show it failing for bugs.
- For LLM features: evaluation sets with expected properties (contains citation, no PII, refuses out-of-scope) run in CI with a pass threshold (`ai-features`).

## 12. Setup snippets

Vitest (`vitest.config.ts`):
```ts
import { defineConfig } from "vitest/config";
export default defineConfig({ test: { environment: "node", setupFiles: ["./tests/setup.ts"], coverage: { provider: "v8" } } });
```
Playwright (`playwright.config.ts`):
```ts
import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  use: { baseURL: process.env.BASE_URL ?? "http://localhost:3000", trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-ar", use: { ...devices["Pixel 7"], locale: "ar-SA" } },
  ],
  webServer: process.env.BASE_URL ? undefined : { command: "npm run dev", port: 3000, reuseExistingServer: true },
});
```
pytest (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
addopts = "-q --strict-markers"
testpaths = ["tests"]
```
