# Debugging methods

## 1. Reproduction template

```
Observed: <what happens>             Expected: <what should happen>
Steps: 1. … 2. … 3. …
Input/data: <ids, payload, file>     Account/role: <user type>
Environment: <local/preview/prod, commit, browser/device, OS, locale ar/en, timezone, network>
Frequency: always / sometimes (x/10) / once
First seen: <date, after deploy/commit?>
Evidence: <error text, request ID, screenshot, logs>
```
Convert to a failing test as soon as possible (unit for logic, integration for endpoints, Playwright for UI flows).

## 2. Reading errors

- Read the whole message and the first stack frame in your code (not library frames).
- `TypeError: Cannot read properties of undefined (reading 'x')` → something upstream returned undefined: find where it should have been set and why it wasn't (failed fetch? wrong key? race?).
- Network errors: open the failing request: status code, response body, request payload, headers (auth, origin).
- Minified production stacks: upload source maps to the error tracker; reproduce with the production build locally (`next build && next start`).
- Database errors: the constraint name tells you which invariant broke.

## 3. Hypothesis log

| # | Hypothesis | Evidence for | Test | Result |
|---|-----------|--------------|------|--------|
| 1 | Session cookie not sent cross-site | 401 only on Safari | Check Set-Cookie SameSite + request cookies in Safari devtools | Confirmed: SameSite=None missing |

Keep it in the PR or issue; it prevents circular guessing (and helps AI agents stay on track).

## 4. Bisecting

```bash
git bisect start
git bisect bad                 # current commit is broken
git bisect good <last-good-sha>
git bisect run pnpm vitest run tests/invoice.test.ts   # exit 0 = good, non-zero = bad
git bisect reset
```
Works for "it used to work". For dependency updates: bisect the lockfile changes or update one package at a time.

## 5. Instrumentation

- **Logs** with context (request ID, IDs, branch taken, durations) at boundaries; remove noisy temporary logs after.
- **Debuggers**: Chrome DevTools (breakpoints, conditional breakpoints, XHR/fetch breakpoints, "pause on exceptions"), VS Code/JetBrains Node and Python debuggers (`node --inspect`, `debugpy`), React DevTools (props/state, profiler), Redux/TanStack Query devtools, Xcode/Android Studio debuggers, Flipper/React Native DevTools.
- **Network**: browser Network tab, `curl -v`, Proxyman/Charles for mobile.
- **Database**: run the query directly; `EXPLAIN ANALYZE`; check RLS by `set role authenticated; set request.jwt.claims…` in Supabase SQL editor.
- **Traces**: OpenTelemetry/Sentry performance to see where time goes.

## 6. Environment diffing ("works locally, not in production")

Check in order: env vars present and correct (names, `NEXT_PUBLIC_` exposure, build-time vs runtime), build mode differences (dev vs prod: strict mode double effects, minification, tree-shaking), runtime (Node vs Edge APIs), data (production data shape, nulls, long strings, Arabic text), region/timezone, caches/CDN (stale responses), feature flags, third-party keys in test vs live mode, CORS/cookies across real domains, file system (serverless is read-only/ephemeral), memory/time limits.

## 7. Bug class catalog

| Class | Symptoms | Confirm | Fix |
|-------|----------|---------|-----|
| Hydration mismatch (SSR) | React hydration warning, flicker, wrong text | Compare server HTML vs client render; look for `Date.now()`, `Math.random()`, `window`, locale formatting in render | Make render deterministic; move client-only values to effects; consistent locale/timezone |
| CORS | Browser "blocked by CORS policy", server logs show OPTIONS | Preflight response headers | Allow-list origins on the server (`launch-security` 13); same-origin API via proxy/rewrites |
| Env var missing | `undefined` config, 500 at startup or on one route | Log presence (not value) at startup; check host env per environment | Startup validation (`launch-security` P1); `.env.example` |
| Stale data / caching | Old values after update | Disable caches stepwise (CDN, framework cache, query cache) | Correct revalidation/invalidation keys; cache headers |
| Auth/session | Random 401s, logged out, works in one browser | Cookies (SameSite, Secure, domain), token expiry/refresh, clock skew | Proper cookie flags, refresh flow, server-side session checks |
| Timezone/date | Off-by-one day, wrong times for Gulf users | Inspect stored values (UTC?), formatting locale/timeZone | Store UTC, format with user timezone; dates as `date` type |
| Race condition | Double charges, duplicates, flaky | Parallel requests in a test; logs with timestamps | Unique constraints, idempotency keys, transactions/atomic updates, disable double submit |
| N+1 / slow query | Slow lists, DB CPU high | Query count per request, `EXPLAIN` | Joins/batching, indexes (`data-design`) |
| Memory leak | Growing memory, slow tab, server OOM | Heap snapshots over time | Remove listeners/intervals on unmount, bounded caches, stream large data |
| Infinite render/effect loop | Freeze, "Maximum update depth" | Effect dependencies, setState in render | Derive state, stable dependencies (`frontend-quality`) |
| Build/deploy-only | Builds locally, fails in CI/host | Node version, lockfile, case-sensitive paths (macOS vs Linux), env at build | Pin versions, `--frozen-lockfile`, fix import casing |
| Mobile-only | Works in browser/simulator, not device | Device logs (Xcode console, `adb logcat`), permissions, network (localhost vs LAN), release build differences | Use device-reachable URLs, handle permissions, test release builds |
| RTL/i18n-only | Broken layout or text in Arabic | Toggle `dir`, check physical CSS, bidi of numbers, plural rules | Logical properties, `<bdi>`, ICU plurals (`i18n-rtl`) |
| Third-party outage | Sudden errors in one integration | Provider status page, error bodies | Timeouts, retries, fallbacks (`error-handling`) |
| Encoding | Garbled Arabic (Ø§Ù„), broken emoji | Charset headers, DB collation, CSV export BOM | UTF-8 everywhere; BOM for Excel CSV |

## 8. Flaky bugs

Record every occurrence with context; look for shared conditions (time, data, concurrency, device); increase logging around the suspected area; stress-test (run 100×, parallel); suspect timing, shared state, external calls, and order dependence.

## 9. Production debugging

- Start from the error tracker issue: release, user, breadcrumbs, request ID → logs → trace.
- Never debug by changing production data or code directly; reproduce in staging with similar data; use feature flags to disable the broken feature if needed.
- Mitigate first (rollback, flag off), then root-cause.

## 10. Postmortem (for incidents and nasty bugs)

Timeline · impact (users, money, data) · root cause (technical + process) · detection (how we found out; could monitoring have caught it earlier?) · fix · prevention actions with owners and dates. Blameless.
