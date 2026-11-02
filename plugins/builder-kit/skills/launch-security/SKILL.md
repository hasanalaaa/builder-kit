---
name: launch-security
description: Load before writing a route handler, server action, login/session, upload, webhook, query/RLS, admin tool, key handling or new package, and for any security review or pre-launch audit. 50 checks (OWASP 2025, ASVS 5, API/LLM Top 10), store rules, reports. Triggers: security, فحص أمني, تأمين.
---

# Launch Security

A complete pre-launch security standard. It has two modes. Pick by the request:

- **BUILD mode**: you are writing or changing app code. Apply the rules in §2 to every line you write, then run the checks that §3 maps to the feature you touched.
- **AUDIT mode**: the user wants the app checked or hardened. Run `references/audit-workflow.md` end to end.

Reference files (load only the ones you need):

| File | Covers |
|------|--------|
| `references/audit-workflow.md` | AUDIT mode step by step and what the final report must contain |
| `references/identity-access.md` | 01 auth · 05 passwords · 09 admin · 15 cookies/sessions · 17 reset links |
| `references/secrets-keys.md` | 02 API keys · 11 env vars · 24 Git history · 25 key rotation |
| `references/data-inputs.md` | 03 database/RLS/IDOR · 06 validation · 07 XSS · 10 injection · 18 uploads · 19 payments |
| `references/network-browser.md` | 04 HTTPS · 12 rate limits · 13 CORS · 14 headers · 16 CSRF |
| `references/deploy-supply-chain.md` | 08 logging · 20 debug mode · 21 vulnerable deps · 22 unused code · 23 exposed files |
| `references/bonus-and-incident.md` | B1 AI features · B2 SSRF · B3 backups · B4 owner accounts · B5 spend caps · B6 privacy · B7 email DNS · incident response |
| `references/review-and-report.md` | 00 app map · 26 full review · 27 test + SECURITY_REPORT.md · maintenance rhythm |
| `references/advanced-hardening.md` | H1–H16: threat modeling, authorization layers, MFA/passkeys/OAuth, crypto, fail-closed, business logic & races, DoS limits, deserialization/XXE/prototype pollution, caching, supply chain & CI, cloud/containers, secrets at scale, CI security pipeline, detection, privacy law, pentest |
| `references/platforms.md` | P1 mobile (MASVS) · P2 desktop (Electron/Tauri) · P3 browser extensions · P4 AI/LLM/agents/MCP · P5 public APIs, SDKs, CLIs |
| `references/store-compliance.md` | S1–S10: App Store & Google Play: IAP/Play Billing, paywall links & disclosures, in-app account deletion, privacy labels/manifest/ATT, Sign in with Apple, permissions, UGC, review hygiene |
| `references/secure-patterns.md` | P1–P16 ready building blocks: validated config, `requireUser`/`requireAdmin`, validated handler + error boundary, owner-scoped queries, Supabase RLS set, password hashing, one-time tokens, safe redirect, origin check, rate limit, headers, payment webhook, upload check, SSRF guard, security log, abuse tests |
| `scripts/security_scan.py` | Static scan of a repo for ~30 common vulnerabilities (secrets, injection, XSS sinks, open redirect, CORS, debug, missing RLS, committed `.env`, unsigned webhooks…), each mapped to its check. Run after every change |
| `scripts/check-exposed.sh` | Probe a domain for exposed sensitive files (check 23) |
| `scripts/find-secrets.sh` | Grep a repo or build folder for secret patterns (checks 02/11/24) |
| `scripts/check-headers.sh` | Check a live URL: HTTPS redirect, security headers, cookie flags, CORS reflection, version leaks (04/13/14/15/20) |

### 0. Classify the project first

Before either mode, decide (from the code) and state in one line:
- **Surfaces:** web front end · backend/API · mobile app · desktop app · browser extension · CLI/SDK · AI/LLM/agent features. Load `platforms.md` sections for each non-web surface, and `store-compliance.md` for anything shipped to the App Store or Google Play.
- **Assurance level** (OWASP ASVS 5.0): **L1** for static/no-account sites; **L2** (default) for any app with user accounts or personal data; **L3** for payments at scale, health, finance, children's data, or high-value targets. L2/L3 means the H-checks in `advanced-hardening.md` are mandatory, not optional.

Each check in the reference files has: **Audit** (what to look for), **Fix** (what correct looks like), **Verify** (the test that proves it), **Done when** (exit criteria). A check is not done until every "Done when" item is true **and proven**.

---

## 1. Rules of work (apply in both modes, always)

1. **Audit before changing.** Show findings before large changes. Never claim something is secure without evidence (a test name, a command and its output, or file:line).
2. **Fix Critical and High directly.** Ask the user first before any change users would notice: logging people out, rotating session secrets, stricter cookies, new rate limits that could block real traffic, blocking a feature, changing a flow.
3. **Root cause, smallest safe change.** Never remove features, weaken another protection, or leave `TODO: secure later`.
4. **Packages.** Before adding one: name it, say why, and confirm on the official registry that it is the real, maintained package (not a typo-squat or an AI-hallucinated name). Prefer what is already installed.
5. **Secrets.** Never print, log, or ask the user to paste a secret value. Refer to it by variable name. When reporting a found secret, show at most the first 4 characters.
6. **Outside the code** (dashboards, hosting, DNS, provider settings): give exact click-by-click steps; mark the item "Needs my action".
7. **Never weaken or delete a test to make it pass.** Fix the code, or explain why the test is wrong.
8. **Never run destructive tests against production or real customer data.** Use localhost/staging and dedicated test accounts (signed-out visitor, user A, user B, admin). Only probe domains the user owns.
9. **Be honest about confidence.** AI review can miss real bugs and invent fake ones. Mark each finding Confirmed (you saw the code path) or Suspected. Do not inflate or hide severity.
10. **Talk to the user in their language** (Arabic if they write Arabic). Code, paths and identifiers stay as-is.

**Finish every check with:**
1. Findings table: `issue · file:line · severity · status (Fixed / Needs my action / Not applicable)`
2. Files changed
3. How the user can verify it themselves in under 5 minutes

---

## 2. BUILD mode: secure-by-default rules

### 2.0 First-attempt protocol (every sensitive feature)

Security is cheapest when it's in the first version. For any feature in the §3 table:
1. **Threat notes first** (H1): 5 lines: what's valuable, who could abuse it, how, and the control for each.
2. **Start from the golden pattern** in `references/secure-patterns.md` (P1–P16). Never hand-write auth checks, validation, tokens, webhooks, uploads or redirects from scratch when a pattern exists; reuse the project's existing helper if it already has one.
   Next.js/TS uploads, Stripe webhooks, owner-scoped CRUD, RLS and AI chat: copy the tested recipe (`recipes` skill: `bk_add.py file-upload|stripe-webhook|owner-scoped-api|postgres-rls|ai-chat-stream`) and adapt it.
3. **Write the abuse tests with the feature** (P16): signed-out → 401, another user's object → 404, extra/tampered fields → 400, foreign origin → 403, over limit → 429.
4. **Scan before calling it done:** `python3 <skill>/scripts/security_scan.py .` → 0 ERROR; every WARN fixed or explained. Then the §3 checks for that feature.
5. **Review the diff against the rules below.**

The rules below are the condensed "Done when" of all 27 checks.

**Identity & access**
- Every protected server entry point (API route, server action, route handler, function, resolver, RPC, cron, webhook) checks auth **inside the handler**, via one helper such as `requireUser()`. UI guards and middleware alone never count. No session → 401.
- The acting user ID always comes from the verified session/token, never from body, query, URL or a client-controlled header.
- JWTs are verified (signature, expiry, issuer, audience) with a library; reject `alg: none`; no hard-coded or weak signing secret. Supabase server code uses `getUser()`/`getClaims()`, not raw cookie trust.
- Admin: one `requireAdmin()` helper on every admin handler; role read from a source users cannot edit (DB roles table, Supabase `app_metadata`, Clerk `publicMetadata`, Firebase custom claims; never `user_metadata`, localStorage, cookies or request params). Deny by default. Not-admin → 403.
- Use a proven auth provider; do not hand-roll auth. Passwords (if you store them): Argon2id (≥19 MiB, 2 iterations, parallelism 1) or bcrypt cost 12, compared with the library verify function. Never log, email, return or store passwords client-side.
- Auth cookies: `HttpOnly`, `Secure`, `SameSite=Lax` (Strict if it doesn't break flows), `Path=/`, `__Host-` prefix where possible. Regenerate session on login, destroy server-side on logout, revoke all sessions on password change/reset.
- Generic auth errors that don't reveal whether an account exists. Redirect params (`next`, `redirect`, `returnTo`) allow only relative same-site paths. OAuth uses `state` and an exact callback allowlist.
- Emailed tokens (reset, magic link, verify, invite): ≥32 random bytes from a CSPRNG, stored as SHA-256 hash, single-use, short-lived (15–30 min reset/magic, ≤24 h verify, ≤7 d invite), invalidated by newer token or password change, link built from `APP_URL` env var, never the Host header.

**Secrets & config**
- Secrets live only in server-side env vars. Never put a secret behind a public prefix (`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`, `EXPO_PUBLIC_`, `PUBLIC_`, `NUXT_PUBLIC_`) or in client/mobile code.
- Client features that need a secret call a narrow server route (auth + validation + rate limit, one specific operation). Never build a generic proxy.
- No insecure fallbacks (`|| "secret"`, `?? "changeme"`). Validate required env vars at startup and fail fast without printing values. Keep `.env*` in `.gitignore`; maintain `.env.example` with placeholders. Separate dev and prod keys and databases.

**Data & inputs**
- Every query by ID is scoped to the current user/tenant (no IDOR). If the browser talks to the DB directly (Supabase/Firebase), RLS/security rules are on for every table and bucket, with separate SELECT/INSERT/UPDATE/DELETE policies and `WITH CHECK` on writes. Views use `security_invoker = true`; `SECURITY DEFINER` functions check permissions themselves.
- Validate every input on the server at the start of the handler with one schema library (Zod, Pydantic…): types, required, number ranges, max length on every string, enums, formats, money as integer minor units. Strict mode: reject unknown fields. Server-owned fields (`id`, `user_id`, `role`, `is_admin`, `price`, `amount`, `status`, `credits`, `balance`, `plan`, `email_verified`…) never come from the client. Clean 400, never a stack trace. Set a max body size.
- Parameterized queries only. Dynamic identifiers (sort column, direction) go through a hard-coded allowlist. NoSQL inputs are type-checked. No shell with user input; use arg arrays.
- Render user content (and AI output) as text. No `dangerouslySetInnerHTML`/`v-html`/`{@html}`/`innerHTML` with user data unless sanitized with DOMPurify or equivalent strict allowlist. User URLs allow only `http:`, `https:`, `mailto:`.
- API responses return only fields the UI needs; never hashes, tokens or other users' private data.
- Uploads: server-side type allowlist checked by magic bytes, size caps (also in presigned policy/bucket), random file names, private storage, signed URLs, `nosniff`, `Content-Disposition: attachment` for non-images, images re-encoded (strip EXIF), no HTML/SVG/JS unless required.
- Payments: client sends only product IDs + quantities; server computes every price/total; fulfil only from signature-verified webhooks (raw body), idempotent by event ID; coupons/credits/stock updated atomically in transactions; entitlements from server-stored subscription status.

**Network & browser**
- HTTPS only; no `http://` URLs (except localhost in dev); TLS to DB and services.
- Rate limit auth, reset, OTP, sign-up, AI/paid, email/SMS and UGC endpoints with a shared store (not in-memory on serverless). 429 + `Retry-After`.
- CORS: exact allowlist from env; never `*` or reflected origin with credentials.
- Security headers on every response (CSP, HSTS, nosniff, frame-ancestors/X-Frame-Options, Referrer-Policy, Permissions-Policy, COOP; remove `X-Powered-By`; `no-store` on personal data).
- CSRF: no state change via GET; framework CSRF protection or token + Origin check on every state-changing request; JSON endpoints require `Content-Type: application/json`; re-auth for email/password change, account deletion, payouts.

**Deploy & ops**
- Debug off in production via env config; global error handler returns generic message + request ID; no public source maps; no seed/test/debug routes in prod.
- Log security events via one helper (`logSecurityEvent`) with UTC time, event, user ID, IP, user agent, request ID, outcome; redact passwords/tokens/cookies/keys; strip newlines.
- New package → verify it is real first; keep lockfile committed.
- AI features: key server-only, auth + per-user rate limit + daily quota + max tokens; treat all user/document content as potentially hostile (prompt injection); model output is untrusted; model tools act only within the user's permissions; destructive/costly actions need confirmation.
- Server fetches of user URLs: http/https only; block private, loopback, link-local and metadata ranges on the initial request and every redirect; timeouts and size caps.

**Design & resilience** (advanced-hardening.md)
- Before a feature that touches money, identity, user data, files, AI or admin power, write short threat notes (STRIDE + "how would I cheat this?") and map each threat to a control or test (H1).
- Authorization at object, property and function level; tenant ID from the session; one central deny-by-default policy (H2).
- Fail closed: errors or timeouts in auth, permission, payment or signature checks deny access. No empty catch blocks. Timeouts on every external call (H5).
- Balances, coupons, stock, credits, one-time actions: atomic updates or locks plus idempotency keys; server-enforced state transitions (H6).
- Every list is paginated with a max page size; body, JSON depth and query time limits; no ReDoS-prone regex on input; GraphQL depth/complexity limits (H7).
- Never deserialize untrusted data unsafely; XML external entities off; file paths never built from input; block `__proto__` keys (H8).
- GitHub Actions pinned to commit SHAs with least-privilege permissions; frozen lockfile installs (H10).

**Mobile, desktop & stores** (platforms.md, store-compliance.md)
- Mobile: no secrets in the bundle; tokens in Keychain/Keystore only; ATS/cleartext off; deep links never act without confirmation; verify App Attest / Play Integrity for abuse-prone actions.
- Desktop (Electron): `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`, validated IPC, signed updates.
- Digital goods inside a store app use Apple IAP / Google Play Billing, verified on the server. Paywalls show Privacy Policy and Terms links, price, period, auto-renewal, and Restore Purchases.
- Any app with accounts lets users delete their account from inside the app (and on the web for Google Play).
- AI agents: tools scoped to the current user's permissions, no generic shell/SQL/HTTP tools, model-generated code only in a sandbox, untrusted content never treated as instructions.

If you must break one of these rules, stop and ask the user. Never ship the shortcut silently.

---

## 3. Feature → checks to (re)run

After building or changing a feature, run these checks from the reference files before calling the work done:

| You added or changed… | Run checks |
|---|---|
| Login or sign-up | 01, 05, 12, 15, 16, 17 |
| A database table | 03, 06, 10 |
| An API route / server action | 01, 03, 06, 09, 12 |
| Comments, profiles, any user text | 06, 07, 12 |
| Payments or subscriptions | 06, 08, 12, 19 |
| File uploads | 18, 03, 12 |
| A third-party API / key | 02, 11, B5 |
| An admin tool | 09, 08, 07 |
| AI / LLM features | 02, 07, 12, B1, B5 |
| Fetching user-supplied URLs | B2, 06 |
| A new package | 21, H10 (verify it is real first) |
| Teams, workspaces, multi-tenant data | 03, 09, H2 |
| Credits, coupons, quotas, referrals, voting | 19, H6 |
| List/search/export endpoints, GraphQL | 06, 10, H7 |
| Login methods, OAuth, MFA, tokens | 01, 15, H3 |
| Encryption or sensitive personal data | 05, H4, H15 |
| Calls to external services | H5, P5 |
| WebSockets / realtime | 01, 03, H9 |
| CI/CD, Docker, cloud infra | 11, 24, H10, H11, H12, H13 |
| AI agents, tools, RAG, MCP | B1, P4, H6, H7 |
| A mobile app or mobile feature | P1, 02, 15 |
| In-app purchases or a paywall | S1, S2, 19 |
| Account sign-up in a store app | S3, S5, 01 |
| A store submission | S1–S10 |
| A desktop app / extension | P2 / P3 |
| Before every launch / major deploy | 23, 20, 26, 27, H13 (+ S1–S10 for store apps) |

---

## 4. AUDIT mode

Read `references/audit-workflow.md` and run it end to end (map → per-check audit → fixes → verify → SECURITY_REPORT.md). Load the check references it names as you reach them.
