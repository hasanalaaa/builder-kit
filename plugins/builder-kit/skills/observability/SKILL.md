---
name: observability
description: Load when launching, adding logging/analytics, or when production fails in ways you can't reproduce. Structured logs with request IDs, Sentry, metrics, tracing, uptime, alerts, Web Vitals. Triggers: logging, monitoring, Sentry, المراقبة, السجلات.
---

# Observability

If you can't see it, you can't fix it. Without logs, errors and metrics, every production issue starts with "it doesn't work" from a user and ends with guessing. The minimum for any launched app: error tracking with releases, structured logs with request IDs, an uptime check, a few dashboards, and alerts that wake someone only for real problems.

| File | Use it for |
|------|-----------|
| `references/signals.md` | The four signal types and what to collect, logging format and levels, request/correlation IDs, Sentry setup per stack, metrics and RED/USE dashboards, OpenTelemetry tracing, uptime/synthetics, alert design and SLOs, product analytics event design, RUM/Web Vitals, mobile crash reporting, privacy/retention, incident basics |
| `scripts/obs_check.py` | Check for an error-tracking SDK, a structured logger, `console.*`/`print` in server code, secrets or tokens passed to log calls, request-ID propagation, health endpoint, Web Vitals reporting, analytics loaded without consent |

## 1. Rules

1. **Errors go to an error tracker** (Sentry or equivalent) on server, client and mobile, tagged with release, environment and user/tenant ID (not email), with source maps uploaded privately.
2. **Logs are structured JSON** with `level`, `msg`, `requestId`, `userId`/`orgId`, `route`, `durationMs`, `err` — one logger module, no raw `console.log` in server code.
3. **Every request has an ID** propagated across services and returned in the response header (`x-request-id`) and in error responses, so support can find the logs.
4. **Never log secrets or sensitive data**: passwords, tokens, API keys, cookies, card data, full request bodies of auth/payment endpoints, health data. Redact at the logger (`launch-security` 08, P15).
5. **Measure what users feel**: request rate, error rate, latency (p50/p95/p99) per route; Web Vitals from real users; key business events (sign-ups, purchases) as metrics.
6. **Alert on symptoms, not causes**: error-rate spikes, latency SLO burn, uptime failure, payment webhook failures, spend anomalies. Every alert is actionable, routed to a person, and has a runbook link. No noisy alerts.
7. **Uptime checks from outside** on the homepage, health endpoint and critical API, every minute, from more than one region.
8. **Product analytics with intent**: a small event plan (`signals.md` §9), consistent names, consent respected, no personal data in event properties unless necessary and disclosed.
9. **Retention and access**: logs kept as long as needed (e.g. 30–90 days), security/audit logs longer, access restricted.

## 2. Workflow: setup (Slice 0 or before launch)

1. Error tracking: Sentry SDKs for each runtime (`signals.md` §4), release + environment tags, source maps, PII scrubbing on.
2. Logger: pino (Node), structlog/loguru (Python), with redaction paths and request-ID middleware.
3. Health endpoint + uptime monitor (Better Stack, UptimeRobot, Checkly, Grafana synthetic).
4. Dashboards: traffic, errors, latency per route; DB health; business events.
5. Alerts with routing (email/Slack/phone) and runbooks.
6. RUM: `web-vitals` → analytics or host (Vercel Speed Insights); mobile crash reporting.
7. Analytics event plan + consent integration (`legal-compliance`).
8. Run `python3 <skill>/scripts/obs_check.py .` → 0 ERROR.

## 3. Done when

- [ ] Error tracker live on all runtimes with releases and source maps; a test error appears with request ID and user ID.
- [ ] Structured logger with redaction; no `console.log` in server code; request IDs end to end.
- [ ] Uptime checks + alerts with runbooks; dashboards for errors, latency, traffic, key events.
- [ ] Web Vitals and mobile crashes reported.
- [ ] Analytics events documented, consent-gated, without unnecessary personal data.
- [ ] `obs_check.py` 0 ERROR.
