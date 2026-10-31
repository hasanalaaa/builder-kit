---
name: error-handling
description: Load before writing code that calls a network, API, DB or AI provider, runs jobs, or handles user input, and when the app crashes, hangs or shows blank screens. One error model, timeouts, retries with backoff, boundaries, no swallowed errors. Triggers: معالجة الأخطاء, شاشة بيضاء.
---

# Error Handling

Missing error handling is the most common reason AI-built apps break in production: the happy path works in the demo, and the first slow network, expired token or full disk shows a blank screen or corrupts data. The rule is simple: every failure is expected, handled at the right place, visible to the user in plain words, and visible to you in logs.

| File | Use it for |
|------|-----------|
| `references/patterns.md` | Error model (TS + Python), boundaries per layer, user messages, timeouts, retries/backoff, circuit breaker, fallbacks, idempotency, React/Next error boundaries, mobile offline, jobs and queues, transactions, checklists |
| `scripts/error_scan.py` | Scan code for empty catch / `except: pass`, catch-and-log-only, bare `except`, `fetch` without `res.ok` check, HTTP calls without timeout, Go ignored errors, Swift `try!`, and a missing app-level error boundary |

## 1. Rules

1. **Never swallow an error.** Every catch either handles it (recovers, retries, falls back with a user-visible state) or rethrows with context. An empty catch or `except: pass` is a bug (`error_scan.py` ERROR).
2. **Fail loudly, early, at the boundary.** Validate inputs at the edge; inside, trust and let real bugs throw (global CLAUDE.md §7).
3. **Two kinds of errors.** *Expected* (validation, not found, conflict, payment declined, offline) → typed results or domain errors with a code and a user message. *Unexpected* (bugs, invariants broken) → crash the request, log with context, show a generic message, alert.
4. **One boundary per layer.** API: one handler wrapper maps errors to the API error format (`api-contracts` §3). UI: route-level error boundaries + per-widget error states. Jobs: one runner that records failures and retries.
5. **Every network call has a timeout.** Fetch, DB, AI, payment, email. No timeout = a hung request = a hung UI = exhausted server.
6. **Retry only what is safe and transient.** Idempotent operations, transient errors (timeouts, 429, 502/503/504, connection resets), exponential backoff with jitter, a max attempt count, and respect for `Retry-After`. Never retry 4xx validation errors or non-idempotent writes without an idempotency key.
7. **Degrade, don't die.** A failing recommendation widget must not take down checkout. Fallbacks: cached data, default value, hidden section, queue for later.
8. **Users get plain words and a next step**; logs get the details (`design-system/references/ux-copy.md` §3). Never show stack traces, SQL or provider error bodies to users (`launch-security` 20).
9. **Keep the user's work.** Form input survives errors; offline actions queue; long edits autosave.
10. **Every error is observable**: logged once with a request ID, error code, user/tenant (not secrets), and sent to error tracking (`observability`).

## 2. Workflow (any code that can fail)

1. List failure modes for the change: invalid input, unauthenticated/forbidden, not found, conflict/duplicate, dependency timeout/down, rate limited, partial failure (some items fail), offline, concurrent edit.
2. For each: where is it detected, where handled, what the user sees, what is logged, is it retried.
3. Implement using `patterns.md` building blocks (shared error class, `withTimeout`, `retry`, boundary).
4. Test the unhappy paths: force dependency failures (mock 500/timeout), invalid input, double submit, offline (`testing-strategy`, `launch-security` H5).
5. Run `python3 <skill>/scripts/error_scan.py .` → 0 ERROR.

## 3. Done when

- [ ] `error_scan.py` 0 ERROR; WARNs fixed or justified with a comment.
- [ ] Every external call has a timeout; retries only on transient + idempotent operations with backoff and a cap.
- [ ] API errors use the shared format; UI shows a designed error state with a recovery action for each failure mode.
- [ ] App-level and route-level error boundaries exist; one widget's failure doesn't blank the page.
- [ ] Unhappy paths have tests (dependency down, timeout, invalid input, conflict).
- [ ] Errors reach logs/error tracking with request ID and context, without secrets or personal data.
