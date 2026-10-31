# Network & Browser: checks 04, 12, 13, 14, 16

Apply SKILL.md §1 "Rules of work" and the "Finish every check with" table to every check here.

---

## 04 · Enforce HTTPS · HIGH

Goal: all traffic encrypted, no plain-HTTP side doors.

**Self-check:** visit `http://domain` and `http://www.domain` → instant redirect to https. Run the domain through SSL Labs (ssllabs.com/ssltest), aim for A. DevTools Console on every main page: no "Mixed Content" warnings.

**Audit**
1. Hosting and TLS handling (platform-managed, Cloudflare, nginx/Caddy on VPS, load balancer).
2. Every HTTP request (apex, www, all subdomains, all paths) permanently redirected (301/308) to HTTPS.
3. Hard-coded `http://` URLs: API calls, images, scripts, fonts, iframes, webhooks, OAuth callbacks, email links, redirects, env var values (localhost in dev config is fine).
4. Server outbound connections (DB, Redis, email, APIs) use TLS; Postgres strings require it (e.g. `sslmode=require`).
5. Cookies marked Secure.
6. Behind a proxy/LB: app reads the original protocol correctly (e.g. Express `app.set('trust proxy', 1)`) so detection and redirects work without loops.

**Fix**
- HTTP→HTTPS redirect at host/proxy level.
- `Strict-Transport-Security: max-age=63072000; includeSubDomains` (includeSubDomains only if every subdomain serves HTTPS). Do NOT add `preload` unless the user explicitly confirms (hard to undo).
- Replace insecure URLs with `https://` or relative URLs.
- Enforce TLS on DB and service connections.

**Verify:** curl commands showing the redirect (`curl -sI http://domain`) and the HSTS header; how to check the console for mixed content.

**Watch out:** forgotten subdomains (staging, blog, docs) often still serve HTTP.

**Done when**
- [ ] HTTP always redirects to HTTPS on every domain and subdomain.
- [ ] HSTS header present on HTTPS responses.
- [ ] No mixed-content warnings.
- [ ] DB and service connections use TLS.
- [ ] Cookies have the Secure flag.

---

## 12 · Rate limiting · HIGH

Goal: nobody can hammer login, forms or paid APIs thousands of times a minute (brute force, credential stuffing, spam, scraping, AI bill abuse).

**Self-check (own app only):**
```bash
for i in $(seq 1 30); do curl -s -o /dev/null -w "%{http_code} " -X POST https://YOURAPP/api/login -H 'content-type: application/json' -d '{}'; done
```
Expect 429s to appear. Repeat for AI, sign-up and contact-form endpoints.

**Audit**
1. Endpoints needing limits, grouped: auth (login, sign-up, reset, OTP/MFA verify, magic links); expensive/paid (AI/LLM, email/SMS, file processing, search, exports); UGC (comments, contact forms); general API.
2. Existing limiting and whether it works on this hosting. In-memory counters do NOT work on serverless or multiple instances.

**Fix**
1. Propose a limits table for user review, starting from:
   - Login: 5/min per IP+email, increasing delays after repeated failures
   - Sign-up: 5/hour per IP
   - Password reset / magic link: 3/hour per email and 10/hour per IP
   - OTP/MFA: 5 attempts per code, then invalidate the code
   - AI/LLM: per-user per-minute limit PLUS daily quota per user/plan
   - Email/SMS sending: strict per-user and global caps
   - General API: generous per-IP (e.g. 100/min)
2. Shared store that works on the host (Upstash Redis + `@upstash/ratelimit`, Redis, the DB, or platform features like Vercel WAF / Cloudflare rate limiting). Key by user ID when signed in, IP otherwise.
3. Correct client IP for the host; don't trust raw spoofable `X-Forwarded-For`; use the platform's verified header.
4. 429 + `Retry-After` + friendly message; never reveals whether an account exists.
5. Log rate-limit hits (check 08).
6. Paid APIs: tell the user how to set hard spending limits in each provider dashboard.

New limits can block real users: ask before enabling on a live app.

**Verify:** script that fires requests at each limited endpoint on localhost/staging and shows the switch to 429.

**Watch out:** SMS endpoints attract fraud ("SMS pumping"): cap hard, restrict destination countries. AI endpoints without quotas are the #1 surprise bill.

**Done when**
- [ ] Login, sign-up, reset, OTP and paid endpoints are rate-limited.
- [ ] Limits use a shared store that works on the hosting.
- [ ] Over-limit requests get 429 with Retry-After.
- [ ] Provider-side spending caps set on AI/email/SMS services.

---

## 13 · Restrict CORS · MEDIUM

Goal: only your own sites can read your API responses from a browser. CORS is not authentication (checks 01, 03 still apply).

**Self-check:**
```bash
curl -s -I -H "Origin: https://evil.example" https://YOURAPP/api/ANY-ENDPOINT
```
If it echoes `Access-Control-Allow-Origin: https://evil.example`, or `*` with `Allow-Credentials: true` → fix.

**Audit**
1. Every CORS config location: `cors()` middleware, framework config (next.config.js headers, vercel.json, netlify.toml/_headers), routes/functions setting `Access-Control-*` manually, Supabase Edge Functions, API gateways, storage bucket CORS (S3, R2, GCS, Firebase Storage).
2. Per location: allowed origins, credentials, methods, headers.
3. Flag: `*`; origins reflected unchecked; `null` allowed; wildcard + credentials; loose matching (`endsWith("app.com")` matches `evilapp.com`; unanchored regex).
4. Is the API even called cross-origin? Same origin may need no CORS at all.

**Fix**
- Explicit allowlist from an env var (production domains; localhost only in dev); exact string matches.
- Credentials only if truly needed, never with a wildcard.
- Restrict methods/headers to what the front end uses.
- Public, read-only, non-personalized endpoints may use `*` but never with cookies.
- One paragraph explaining CORS ≠ auth, and confirm endpoints still enforce auth server-side.

**Verify:** curl showing allowed origin gets CORS headers and unknown origin gets none.

**Watch out:** curl/scripts/servers ignore CORS entirely. Buckets have their own CORS settings.

**Done when**
- [ ] No wildcard or reflected origin on endpoints using cookies or returning private data.
- [ ] Origins are an exact allowlist from config.
- [ ] Unknown origins get no `Access-Control-Allow-Origin`.

---

## 14 · Security headers · MEDIUM

Goal: switch on browser protections on every response.

**Self-check:** securityheaders.com → aim for A. Or `curl -s -I https://YOURAPP` and look for `content-security-policy`, `strict-transport-security`, `x-content-type-options`, `x-frame-options`, `referrer-policy`.

**Audit**
1. Which headers are sent now and where they're configured (framework config, middleware, helmet, vercel.json, netlify _headers, nginx/Caddy).
2. Every third-party origin the app legitimately loads/connects to (analytics, fonts, Stripe, Supabase, auth provider, image CDN, AI API, maps), found in code. Needed for CSP.

**Fix** (one place, appropriate for the stack, all routes)
- `Content-Security-Policy` starting from: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests`. Add only the specific third-party origins found. Avoid `'unsafe-inline'`/`'unsafe-eval'` for scripts; use nonces/hashes. Justify any unsafe value.
- `Strict-Transport-Security: max-age=63072000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (SAMEORIGIN if own pages must be framed)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()` (enable only used features)
- `Cross-Origin-Opener-Policy: same-origin` (`same-origin-allow-popups` if OAuth/payment popups break)
- Remove `X-Powered-By` and server version headers.
- `Cache-Control: no-store` on authenticated pages and API responses with personal data.

**Rollout:** ship CSP first as `Content-Security-Policy-Report-Only`; list what would be blocked on each main page (login, checkout, OAuth, payments, uploads, embeds); adjust; then enforce. Tell the user exactly which pages to click through.

**Verify:** curl command confirming every header; expected securityheaders.com grade.

**Watch out:** a broken CSP silently breaks payments, OAuth popups, analytics. Headers in next.config.js don't apply on every host setup: verify on the live URL.

**Done when**
- [ ] All listed headers present on every page and API response.
- [ ] CSP enforced (not just report-only) and login, checkout, OAuth still work.
- [ ] `X-Powered-By` gone.
- [ ] securityheaders.com grade A or better.

---

## 16 · CSRF protection · HIGH

Goal: other sites can't make logged-in users perform actions.

**Self-check:** cookie-based login → CSRF applies. Any GET that changes data (`/delete?id=`, `/logout`, `/subscribe`)? On own app: save a local HTML file with an auto-submitting form posting to an endpoint, open while logged in, see if the action happens.

**Audit**
1. How requests authenticate. Cookies (incl. provider-managed) → CSRF applies. Only a JS-added bearer token in `Authorization` → low risk; say so and confirm no cookie path exists.
2. Every state-changing endpoint (POST/PUT/PATCH/DELETE, server actions, form handlers) and every state-changing GET.
3. Existing protection: framework CSRF middleware (Django/Rails/Laravel built-in), Next.js Server Actions Origin/Host check (is `serverActions.allowedOrigins` loosened?), SameSite, custom token/Origin checks.
4. JSON endpoints that also accept form-encoded or `text/plain` bodies (sendable cross-site without preflight).

**Fix**
- Move state-changing GETs to POST/DELETE.
- Use built-in framework CSRF protection; ensure it isn't disabled. Express/custom: a maintained synchronizer or signed double-submit token library (old `csurf` is deprecated).
- Origin check on every state-changing request as defence in depth: reject if Origin present and not own site.
- JSON endpoints require `Content-Type: application/json`.
- Auth cookies SameSite=Lax/Strict (check 15).
- Exempt only webhooks, which verify signatures (check 19).
- High-risk actions (change email/password, delete account, payouts): require current password or recent re-login.

**Verify:** test that a state-changing request with a foreign Origin and no CSRF token is rejected, and the real UI still works.

**Watch out:** SameSite alone isn't complete (uncontrolled subdomains, old browsers). Login CSRF is real: protect the login form.

**Done when**
- [ ] No GET request changes data.
- [ ] All state-changing requests require a CSRF token or pass an Origin check.
- [ ] Cookies use SameSite=Lax or Strict.
- [ ] Sensitive account changes require re-authentication.
