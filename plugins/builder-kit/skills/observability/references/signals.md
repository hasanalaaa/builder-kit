# Observability signals

## 1. Signals

| Signal | Answers | Tools |
|--------|---------|-------|
| Errors | What broke, for whom, since which release | Sentry, Bugsnag, Rollbar, Highlight |
| Logs | What happened in this request/job | Host logs + Axiom, Better Stack, Datadog, Grafana Loki, CloudWatch |
| Metrics | How much, how fast, how often (trends, alerts) | Prometheus/Grafana, Datadog, host metrics, PostHog for product metrics |
| Traces | Where the time went across services/DB/external calls | OpenTelemetry → Sentry/Honeycomb/Grafana Tempo/Datadog |
| Uptime / synthetics | Is it up and working from outside | Better Stack, Checkly, UptimeRobot, Grafana synthetics |
| RUM | What real users experience (Web Vitals, JS errors) | web-vitals lib, Vercel Speed Insights, Sentry, PostHog |
| Product analytics | What users do (funnels, retention) | PostHog, Amplitude, Mixpanel, Plausible/Umami (privacy-first page analytics) |

## 2. Logging

Format (JSON, one line per event):
```json
{"level":"info","time":"2026-10-31T09:00:00.000Z","msg":"invoice.sent","requestId":"req_01J…","userId":"u_123","orgId":"o_9","route":"POST /api/invoices/:id/send","durationMs":142,"invoiceId":"inv_77"}
```
Levels: `error` (needs attention), `warn` (unexpected but handled), `info` (business events, request summary), `debug` (off in production by default).

Node (pino):
```ts
import pino from "pino";
export const log = pino({
  level: process.env.LOG_LEVEL ?? "info",
  redact: { paths: ["req.headers.authorization", "req.headers.cookie", "*.password", "*.token", "*.apiKey", "*.secret", "*.cardNumber"], censor: "[redacted]" },
});
```
Python (structlog): JSON renderer, `contextvars` for request ID, processor that drops sensitive keys.

Rules: log once per request (summary line) + notable events; errors logged once at the boundary with stack; no logging inside tight loops; no PII beyond IDs.

## 3. Request IDs and correlation

- Middleware: read incoming `x-request-id` (from proxy/CDN) or generate one (`crypto.randomUUID()`), store in async context (AsyncLocalStorage / contextvars), add to every log line, return it as a response header, include in error JSON (`requestId`) and in Sentry scope.
- Pass it to downstream services and jobs (headers, job payload).
- Show it to users on error pages ("Reference: req_01J…") for support.

## 4. Error tracking setup

- **Next.js**: `@sentry/nextjs` wizard (client, server, edge configs), `instrumentation.ts`, tunnel route to avoid ad-blockers, source maps uploaded in CI with auth token as secret, `release` = commit SHA.
- **React SPA**: `@sentry/react` + error boundary integration + router instrumentation.
- **Node/Python APIs**: SDK init at startup, framework integration (Express/Fastify/Hono/FastAPI/Django), capture unhandled rejections.
- **Expo/React Native**: `@sentry/react-native` with Expo plugin, source maps/dSYMs via EAS.
- **iOS/Android native**: Sentry or Firebase Crashlytics with dSYM/mapping upload.
- Configure: `environment`, `release`, `sendDefaultPii: false`, `beforeSend` scrubbing, sample rates (errors 100%, traces 5–20%), ignore noisy browser extension errors, user context with ID only.
- Workflow: triage new issues weekly; assign; link to fix PR; mark resolved in release.

## 5. Metrics and dashboards

- **RED** per service/route: Rate, Errors, Duration (p50/p95/p99).
- **USE** for resources: Utilization, Saturation, Errors (DB connections, CPU, memory, queue depth).
- **Business**: sign-ups, activations, purchases, MRR events, AI spend, emails sent/bounced.
- Dashboards: "Is it healthy?" (one screen: uptime, error rate, p95, traffic, deploy markers), "Database", "Jobs/queues", "Business", "Costs".

## 6. Tracing

- OpenTelemetry SDK (Node `@opentelemetry/sdk-node` or Next.js `@vercel/otel`, Python `opentelemetry-instrumentation-*`), auto-instrument HTTP, DB, fetch.
- Export to Sentry/Honeycomb/Grafana/Datadog; sample (head 5–20%, keep all errors).
- Use traces to find N+1 queries, slow external calls and serial awaits.

## 7. Uptime and synthetics

- Check every minute from 2+ regions: homepage (200 + expected text), `/api/health` (DB reachable, version), login page, a critical API.
- Synthetic browser check of the main flow (Checkly/Playwright) every 10–30 minutes on production with a test account.
- SSL expiry and domain expiry monitors.
- Public status page for customers when you have SLAs.

## 8. Alerts and SLOs

- Define SLOs for user journeys: e.g. 99.9% of requests to `/api/*` succeed; 95% under 500 ms; checkout success ≥ 99%.
- Alert on SLO burn rate (fast burn → page; slow burn → ticket), uptime check failures (2 regions), error-rate spike vs baseline, payment/webhook failure, queue backlog, AI/cloud spend anomaly, certificate expiry.
- Each alert: owner, severity, runbook link (what to check, how to roll back), auto-resolve.
- Review alerts monthly: delete noisy ones, add missing ones after incidents.

## 9. Product analytics

Event plan (keep it small, in the repo as `analytics/events.md`):
| Event | When | Properties |
|-------|------|-----------|
| `signed_up` | account created | method, referrer |
| `onboarding_completed` | checklist done | steps, duration |
| `<core_action>` | the product's main value action | type |
| `subscription_started` | paid conversion | plan, interval |
| `subscription_canceled` | cancel | plan, reason |

- Naming: `object_action` past tense, snake_case; properties typed; identify users by internal ID; group by org for B2B.
- Server-side events for anything money-related (reliable, not ad-blocked).
- Consent: no non-essential analytics cookies/IDs before consent where the law requires (`legal-compliance`); cookieless/aggregate analytics as fallback.
- Funnels, retention cohorts, feature adoption; review with the spec's success metrics.

## 10. Real-user Web Vitals

```ts
import { onCLS, onINP, onLCP } from "web-vitals/attribution";
const send = (m) => navigator.sendBeacon("/api/vitals", JSON.stringify({ name: m.name, value: m.value, rating: m.rating, page: location.pathname, attribution: m.attribution }));
onLCP(send); onINP(send); onCLS(send);
```
Or the host's built-in (Vercel Speed Insights, Cloudflare Web Analytics). Track p75 per template; alert on regressions after deploys.

## 11. Mobile

- Crash-free sessions/users rate (target > 99.5%), ANRs (Android), app start time, slow/frozen frames, network errors, OTA update adoption.
- Upload dSYMs/ProGuard mappings each build; tag release and build number.
- Breadcrumbs for navigation; user ID; device/OS info (built in).

## 12. Privacy and retention

- Treat logs as personal data when they contain IDs/IPs; document in privacy policy; retention limits; access control; deletion requests may need log purges or anonymization.
- Session replay tools: mask all inputs and text by default; disable on sensitive pages; consent where required.

## 13. Incident basics

- Severity levels (SEV1 users can't use core product / data at risk; SEV2 major feature broken; SEV3 minor).
- During: one incident lead, status updates every 30 min, mitigate first (rollback, flag off, scale), then fix.
- After: blameless postmortem within a week: timeline, impact, root cause, what went well/poorly, action items with owners. Security incidents follow the `launch-security` incident card.
