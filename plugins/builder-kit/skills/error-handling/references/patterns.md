# Error-handling patterns

## 1. Error model

### TypeScript
```ts
// shared/errors.ts: the only error classes the app throws on purpose
export type ErrorCode =
  | "validation_failed" | "unauthenticated" | "forbidden" | "not_found"
  | "conflict" | "rate_limited" | "dependency_failed" | "internal";

const STATUS: Record<ErrorCode, number> = {
  validation_failed: 400, unauthenticated: 401, forbidden: 403, not_found: 404,
  conflict: 409, rate_limited: 429, dependency_failed: 502, internal: 500,
};

export class AppError extends Error {
  constructor(
    public code: ErrorCode,
    public userMessage: string,                 // safe to show
    public details?: Record<string, unknown>,   // safe to log, never secrets
    options?: { cause?: unknown },
  ) {
    super(`${code}: ${userMessage}`, options);
  }
  get status() { return STATUS[this.code]; }
}
```
Wrap causes: `throw new AppError("dependency_failed", "Payment service is unavailable. Try again in a minute.", { provider: "stripe" }, { cause: err })`.

For expected outcomes in business logic, a result type is often clearer than throwing:
```ts
export type Result<T, E = AppError> = { ok: true; value: T } | { ok: false; error: E };
```
Use results where callers must handle the failure (payment declined, slot taken); throw for "should not happen" and for unrecoverable request failures.

### Python
```python
class AppError(Exception):
    status = 500
    code = "internal"
    def __init__(self, user_message: str, **details):
        super().__init__(user_message)
        self.user_message, self.details = user_message, details

class NotFound(AppError): status, code = 404, "not_found"
class Conflict(AppError): status, code = 409, "conflict"
class DependencyFailed(AppError): status, code = 502, "dependency_failed"
# raise DependencyFailed("Payment service is unavailable.", provider="stripe") from err
```

## 2. Boundaries

**API (one wrapper)**: see `launch-security/references/secure-patterns.md` P3 `handleError`. Map `AppError` → its status and problem JSON; map validation library errors → 400 with field errors; everything else → 500 generic message + log with stack + requestId.

**FastAPI**:
```python
@app.exception_handler(AppError)
async def app_error(request, exc: AppError):
    return JSONResponse(status_code=exc.status, media_type="application/problem+json",
        content={"type": f"/errors/{exc.code}", "title": exc.user_message, "status": exc.status,
                 "code": exc.code, "requestId": request.state.request_id})
```

**React / Next.js**:
- App Router: `app/error.tsx` (route segment), `app/global-error.tsx` (root), `not-found.tsx`. Each shows a designed message + "Try again" (`reset()`) + a way home.
- Wrap independent widgets in their own boundary (`react-error-boundary`) so one failing chart doesn't blank the dashboard.
- Data fetching: TanStack Query `isError` state per query with retry button; don't render `undefined.map`.
- Event handlers and async code are not caught by error boundaries: handle them (toast/inline error) explicitly.

**React Native / Expo**: a root error boundary with a "Restart" action (`expo-updates` `reloadAsync`), Sentry native crash reporting, per-screen error states.

**Swift**: `do/catch` with typed errors, show an alert or inline state; avoid `try!` (crash) and blanket `try?` (silent nil) on operations whose failure matters.

**Jobs/queues**: runner catches per job, records `attempts`, `last_error`, `failed_at`; retries with backoff; moves to a dead-letter state after N attempts; alerts on dead letters.

## 3. Timeouts

```ts
export async function fetchWithTimeout(url: string, init: RequestInit = {}, ms = 10_000) {
  const res = await fetch(url, { ...init, signal: AbortSignal.timeout(ms) });
  if (!res.ok) throw new AppError(res.status === 429 ? "rate_limited" : "dependency_failed",
    "A service we depend on didn't respond correctly. Please try again.", { url: new URL(url).host, status: res.status });
  return res;
}
```
- Python: `httpx.Client(timeout=httpx.Timeout(10.0, connect=3.0))`; `requests.get(url, timeout=(3, 10))`.
- DB: statement timeout (`set statement_timeout = '5s'` per role or per query), pool acquire timeout.
- AI calls: longer (30–120s) but always bounded, streamed when user-facing.
- Overall request budget: the sum of downstream timeouts must be below the platform's function timeout.

## 4. Retries with backoff and jitter

```ts
export async function retry<T>(fn: () => Promise<T>, { attempts = 3, baseMs = 300, maxMs = 5_000,
  retryable = (e: unknown) => e instanceof AppError && ["dependency_failed", "rate_limited"].includes(e.code) } = {}) {
  for (let i = 1; ; i++) {
    try { return await fn(); }
    catch (e) {
      if (i >= attempts || !retryable(e)) throw e;
      const delay = Math.min(maxMs, baseMs * 2 ** (i - 1)) * (0.5 + Math.random()); // full jitter
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}
```
- Python: `tenacity` (`@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(max=5), retry=retry_if_exception_type(TransientError))`).
- Respect `Retry-After`.
- Retry only idempotent operations, or include an idempotency key (Stripe and most payment APIs accept one).
- Don't stack retries in several layers (client × server × SDK = 27 attempts).

## 5. Circuit breaker and fallbacks

When a dependency is failing, stop hammering it:
- Track recent failures per dependency; after N failures in a window, "open" the circuit and fail fast (or use the fallback) for a cool-down period; then allow a probe request.
- Libraries: `opossum` (Node), `pybreaker` (Python), or the provider SDK's built-in retry policy.
- Fallbacks by feature: cached last-good data (with "updated 5 min ago"), defaults, hide the optional widget, queue the action ("We'll send it when the service is back"), alternative provider (AI model fallback, secondary email provider).

## 6. Partial failures

- Bulk operations return per-item results: `{ succeeded: [...], failed: [{ id, code, message }] }` and the UI shows both.
- Multi-step writes: a DB transaction, or a saga with compensating actions when steps span services (charge → create order → if order fails, refund).
- Outbox pattern for "write to DB + send event/email": write the event row in the same transaction, a worker delivers it.

## 7. Client-side and mobile

- Every async UI action: pending → success | error states, button disabled while pending, error message near the action with "Try again".
- Optimistic updates roll back on failure and tell the user.
- Offline: detect (`navigator.onLine` + failed requests / NetInfo), show a banner, serve cached data, queue mutations with retry on reconnect; resolve conflicts explicitly (last-write-wins only when acceptable).
- Never lose typed input: keep state across errors, autosave drafts (localStorage/IndexedDB/AsyncStorage).

## 8. Logging errors

- Log once at the boundary (not at every layer) with: `requestId`, `code`, `route`, `userId`/`orgId`, dependency, duration, stack for unexpected errors.
- Redact secrets, tokens, passwords, card data, and personal data (`launch-security` P15 `logSecurityEvent`).
- Send unexpected errors to Sentry (or equivalent) with release and environment tags; alert on new error types and spikes (`observability`).

## 9. Anti-patterns (error_scan.py catches several)

| Anti-pattern | Instead |
|--------------|---------|
| `catch (e) {}` / `except: pass` | handle, or rethrow with context |
| `catch (e) { console.log(e) }` and continue as if fine | handle or rethrow; log at the boundary |
| `except Exception:` around everything | catch the specific exceptions you can handle |
| `fetch()` without checking `res.ok` | throw on non-2xx |
| `requests.get(url)` without `timeout` | always pass timeout |
| returning `null` on failure so the caller renders "No data" | return a typed error; show an error state |
| `alert(error.message)` / showing provider errors | user message + log details |
| retrying a POST that charges money | idempotency key or no retry |
| `if err != nil { }` / `_ = err` (Go) | handle or return wrapped error |
| `try!` (Swift), `!!` on network data (Kotlin) | handle the failure |
