# Identity & Access: checks 01, 05, 09, 15, 17

Apply SKILL.md §1 "Rules of work" and the "Finish every check with" table to every check here.

---

## 01 · Proper authentication · CRITICAL

Goal: the server proves who the user is on every request. A login screen or hidden menu is UI, not security.

**Self-check (user can run):** copy an API request as cURL, delete the cookie/Authorization line, run it → expect 401. Open a protected page logged out in a private window → redirect + failed data request. Change an ID in the URL/body (`/api/users/42` → `/43`) → never someone else's data.

**Audit**
1. Identify the auth method (Supabase Auth, Clerk, Auth.js/NextAuth, Firebase, custom JWT, server sessions). If hand-rolled, say so and recommend a proven provider.
2. List EVERY server entry point: API routes, server actions, route handlers, edge/serverless functions, GraphQL resolvers, RPC/DB functions, webhooks, cron routes. For each: needs a signed-in user? Is it checked **on the server inside the handler** (not only UI, client route guard, or middleware)?
3. Identity is verified each request: server-side session lookup, or JWT verified by a library (signature, expiry, issuer, audience). Flag tokens decoded without verification, `alg: none`, hard-coded or weak signing secrets.
4. The user ID used for reads/writes comes only from the verified session/token, never body/query/URL/client header.
5. Sign-up/login: generic errors ("Invalid email or password"); email verification before sensitive actions; sessions invalidated on logout and password change; sensible session lifetime.
6. OAuth/social/magic links: `state` parameter used; callback/redirect URLs are an exact allowlist; `?next=`/`?redirect=`/`?returnTo=` allow only relative same-site paths (no open redirect).

**Fix**
- One reusable server helper (`requireUser()` / `getCurrentUser()`) called at the top of every protected handler; 401 without a valid session.
- Remove every security decision that relies only on client code.
- Supabase server-side: use `getUser`/`getClaims` (re-validates with auth server), not cookie-as-is.

**Verify:** for every protected endpoint, a credential-less curl that must return 401, and one that reads another user's resource and must return 403/404.

**Watch out:** middleware (`proxy.ts` since Next.js 16) alone is not enough (a 2025 Next.js flaw let attackers skip middleware entirely). Next.js server actions are public endpoints; each needs its own check. Don't roll your own auth.

**Done when**
- [ ] Every protected endpoint returns 401 without a valid session.
- [ ] User ID always comes from the verified session.
- [ ] Logout and password change kill existing sessions.
- [ ] Login/sign-up errors don't reveal whether an email is registered.
- [ ] Redirect params allow only your own paths.

---

## 05 · Hash passwords · CRITICAL

Goal: stored passwords are unreadable even to you or a database thief.

**Self-check:** good hashes start like `$argon2id$`, `$2b$12$`, `$scrypt$`; plain text or a 32/64-char hex string is bad. Search logs/error tracker for a test password → must not appear. No API response (incl. `/api/me`, admin user lists) contains `password`/`password_hash`.

**Audit**
1. Find every password touchpoint: sign-up, login, change, reset, admin create-user, invites, seed scripts, imports, tests.
2. If an auth provider stores passwords, confirm the app does NOT also store/log/forward them (own users table, analytics, logs, emails, error tracking).
3. If the app stores them: plain text, reversible encryption, MD5, SHA-1, SHA-256 or any fast/unsalted hash = Critical.
4. Comparison uses the library's constant-time verify, not `==` on hashes.
5. Request loggers, error handlers and Sentry etc. never record bodies with passwords.
6. No response or client state includes a password/hash; never in localStorage or cookies.

**Fix**
- Argon2id (OWASP minimum: 19 MiB memory, 2 iterations, parallelism 1) via a maintained library, or bcrypt cost 12 (min 10). bcrypt uses only the first 72 bytes: set a max length accordingly.
- Weak existing hashes: on next successful login, verify against old hash and immediately re-hash. Propose what to do for users who never return (e.g. force reset).
- Policy (NIST-style): min 8 chars (12+ recommended), allow ≥64, allow all characters incl. spaces, no composition rules. Optional: block breached passwords via Have I Been Pwned range API (k-anonymity).
- Redact password fields from all logs and error reports. Never email a password.

**Verify:** show a current stored hash format; test that correct password logs in, wrong fails, plain password appears in no log output.

**Watch out:** encryption is not hashing. Full-body request loggers will log passwords.

**Done when**
- [ ] Stored with Argon2id, scrypt or bcrypt (or fully by an auth provider).
- [ ] No password or hash in logs, error reports, emails or API responses.
- [ ] Migration path exists for old weak hashes.
- [ ] Password rules are length-based, not symbol rules.

---

## 09 · Lock down admin routes · CRITICAL

Goal: the server checks the admin role on every admin request. Hidden buttons and secret URLs don't count.

**Self-check:** as a normal user visit `/admin` → redirect or 403. Copy an admin API request as cURL, swap in a normal user's cookie → 403. Search the front-end bundle for admin emails or `isAdmin` logic.

**Audit**
1. List every admin/staff/internal/privileged route: pages, API routes, server actions, GraphQL mutations, DB functions, cron/job endpoints, and seed/test/debug/migration routes (`/api/seed`, `/api/test`, `/api/reset-db`…).
2. For each: role checked on the SERVER inside the handler, for the page and every data endpoint it calls?
3. Role source. OK: DB roles column/table, Supabase `app_metadata`, Clerk `publicMetadata`, Firebase custom claims. NOT OK: Supabase `user_metadata` (user-editable), localStorage, client-set cookie, request param, hard-coded email check in front-end.
4. Admin emails or endpoint names exposed in the client bundle?

**Fix**
- One `requireAdmin()` that loads the verified user AND checks the role from a trusted source; 403 otherwise. Call at top of every admin handler (not only middleware/layout).
- Deny by default: new admin routes protected unless explicitly public.
- Cron/webhook/internal endpoints: long random secret in a header compared in constant time, or the platform's built-in cron auth.
- Remove seed/test/debug endpoints from production builds or block by environment.
- Log every admin action (who, what, when, target) with the check-08 logger.
- Tell the user how to require MFA for admin accounts in their auth provider.

**Verify:** tests: signed-out → 401; normal user → 403 on every admin page and endpoint; admin → allowed; a user cannot make themselves admin by editing their profile/metadata.

**Watch out:** "Nobody knows the URL" is not protection; URLs end up in bundles, logs and history.

**Done when**
- [ ] Every admin page and API checks the role on the server.
- [ ] Roles live where users can't edit them.
- [ ] Normal users get 403 everywhere admin-related (tested).
- [ ] Seed/test/debug routes are gone from production.
- [ ] Admin actions are logged.

---

## 15 · Secure session cookies · HIGH

Goal: the login cookie can't be read by scripts, sent over HTTP, or abused cross-site.

**Self-check:** DevTools → Application → Cookies: session cookie has HttpOnly ✓, Secure ✓, SameSite Lax/Strict. Local Storage has nothing named `token`, `jwt`, `session`, `access_token`. After logout, replaying an old request with the old cookie fails.

**Audit**
1. Where session state lives: server store, cookies (which library), JWTs, localStorage/sessionStorage, provider SDK. List every cookie and its flags.
2. Each auth cookie: HttpOnly, Secure, SameSite Lax/Strict, `Path=/`, no overly broad `Domain`, sensible Max-Age/Expires.
3. Lifecycle: session ID regenerated on login and privilege change (anti-fixation)? Destroyed server-side on logout? Idle timeout + absolute max lifetime? All sessions revoked after password change/reset?
4. Tokens in localStorage/sessionStorage: explain the risk; does the provider support cookie sessions?
5. JWTs: short-lived access + refresh-token rotation; how revocation works; no sensitive data in payload (it's readable).

**Fix**
- HttpOnly + Secure + SameSite=Lax on all auth cookies (Strict for extra-sensitive apps if flows survive). `__Host-` prefix where the framework allows.
- Regenerate on login, destroy on logout, "log out of all devices" that runs automatically after password change.
- Sensible lifetimes (e.g. 7–30 days + idle timeout for consumer apps; shorter for admin). Explain the choice.
- If the provider manages cookies, confirm defaults are secure and code doesn't override them insecurely.
- No secrets/personal data in readable cookies; sign or encrypt any data cookie with a strong secret.

**Verify:** list final cookies with flags; test proving a logged-out cookie no longer works.

**Watch out:** some SDKs default to localStorage; acceptable only with strong CSP and conscious choice. SameSite=Strict can break email/OAuth redirects; Lax is the usual default.

**Done when**
- [ ] Session cookies have HttpOnly, Secure and SameSite.
- [ ] No long-lived tokens in localStorage, or the risk is understood and mitigated.
- [ ] Logout and password change invalidate sessions server-side.
- [ ] Sessions expire on a sensible schedule.

---

## 17 · Password-reset links expire · HIGH

Scope: password reset, magic-link login, email verification, email-change confirmation, team invites, any emailed/SMS link or code granting access.

**Self-check:** use a reset link, click it again → fails. Request two resets → first link dead. Reset for a non-existent email → identical message. Wait past expiry → fails.

**Audit:** per flow report: token generation, storage, lifetime, single-use?, what invalidates it, response for unknown emails, how the link URL is built.

**Fix** (if a provider like Supabase/Clerk/Firebase owns the flow, show which provider settings to check and only change code the user owns)
1. Tokens from a CSPRNG, ≥32 bytes (`crypto.randomBytes(32)` / `secrets.token_urlsafe(32)`). Never timestamps, user IDs, UUIDv1, `Math.random`.
2. Store only a SHA-256 hash of the token.
3. Expiry: 15–30 min reset & magic link; ≤24 h email verification; ≤7 days invites.
4. Single use; new request or password change invalidates all outstanding tokens for that user.
5. Same message and similar response time whether or not the email exists ("If an account exists, we've sent a link").
6. Rate limit per email and per IP (check 12).
7. Build the link from `APP_URL` env var, NEVER from the Host header (host-header poisoning).
8. Reset page: `Referrer-Policy: no-referrer`; no third-party scripts (analytics can capture the token).
9. After reset: normal password policy + hashing (05), revoke all sessions, email a "your password was changed" notice.
10. Allowlist post-flow redirect URLs.

**Verify:** tests: used token fails; expired fails; older fails after newer issued; real vs fake email responses identical; forged Host header doesn't change link domain.

**Done when**
- [ ] Tokens are random (32 bytes), stored hashed, expire in 15–30 minutes.
- [ ] Links are single-use; a new one kills the old one.
- [ ] Responses don't reveal whether an email is registered.
- [ ] Links are built from configured URL, not Host header.
- [ ] A reset logs out all other sessions and notifies the user.
