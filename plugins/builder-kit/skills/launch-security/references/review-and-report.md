# App map (00), full review (26), proof + report (27), maintenance

Apply SKILL.md §1 "Rules of work" throughout.

---

## 00 · Project context + map the app (run first, no code changes)

**Project context block** (fill from code; ask only for what you can't determine). Put it at the top of `SECURITY_MAP.md` and reuse it for every later check:

```
PROJECT CONTEXT
- What the app does:
- Who uses it: public consumers / team / businesses
- Built with: Lovable / Bolt / v0 / Cursor / Claude Code / Replit / other
- Stack:
- Hosting:
- Auth:
- User roles:
- Sensitive data: emails, addresses, payments, health, messages, files…
- Status: not launched / live with N users
- Concerns:
```

**Inspect the whole codebase. Do NOT modify application code.** Create `SECURITY_MAP.md` with:
1. **Stack:** languages, frameworks and versions, package manager, hosting/deploy target.
2. **Data:** database(s) and how reached (server-only, or directly from browser via Supabase/Firebase SDKs); every table/collection and its sensitivity.
3. **Auth:** provider/method, where the session lives, where checks happen, user roles.
4. **Entry points:** table of EVERY page, API route, server action, edge/serverless function, webhook and cron job: `path · method · purpose · requires login? · roles allowed · inputs accepted`.
5. **Third-party services:** each one, purpose, which key, client-side or server-side.
6. **Environment variables:** names only (NEVER values), where used, public vs secret.
7. **Risky features:** file uploads, payments, emails/SMS, AI/LLM calls, anything fetching URLs, admin tools, imports/exports.
8. **Questions:** anything not determinable from code.

End with the **TOP 5 security concerns**, ranked, plain language, each mapped to the check number that addresses it. No fixes yet. Keep the map updated as the app changes.

---

## 26 · Thorough security review (attacker's view) · REVIEW

Run after checks 01–25, in a fresh session with full codebase access if possible. **Do NOT change code in this step.** Produce the report first.

**Phase 1 · Attack surface:** read the code (and `SECURITY_MAP.md`). Summarize stack, hosting, data and sensitivity, roles, every entry point (pages, API routes, server actions, functions, webhooks, cron, uploads, admin tools), third-party services, trust boundaries (what the browser controls vs what the server decides).

**Phase 2 · Review each area** (list what you checked and what you found):
1. Auth: server-side checks on every endpoint, sessions, password reset, OAuth/redirects, MFA for admins.
2. Access control: IDOR on every ID-based endpoint, admin routes, multi-tenant/team isolation, role changes.
3. Secrets: client bundle, env vars, Git history, logs, exposed files.
4. Data: DB rules/RLS, least privilege, sensitive fields in responses, backups.
5. Inputs: server validation, mass assignment, SQL/NoSQL/command injection, XSS (incl. AI output), open redirects, SSRF in URL-fetching features, email header injection.
6. Files: upload type/size/content, storage privacy, serving.
7. Payments: server-side pricing, webhook verification, idempotency, entitlements, coupons, race conditions.
8. Network: HTTPS/HSTS, CORS, headers, cookies, CSRF, rate limiting (esp. paid/AI).
9. Packages & deployment: vulnerable/suspicious deps, debug mode, error leakage, source maps, preview deployments.
10. Business logic: abuse of free trials, referrals, credits, invites, quotas; state transitions (can steps be skipped or repeated?); race conditions; anything unique to this app (e.g. inviting yourself into someone else's team by guessing its ID).
11. AI features: prompt injection via user content/documents, tools the model can trigger, cross-user data leaks, cost abuse.

**Phase 3 · Write `SECURITY_REVIEW.md`:**
- Executive summary in plain language (max 5 lines).
- Findings table sorted by severity: `ID · title · severity (Critical/High/Medium/Low) · location (file:line or endpoint) · step-by-step exploit · recommended fix · effort (S/M/L) · confidence · status`.
- What was checked and found clean (coverage).
- What could NOT be verified from code (dashboard settings, hosting config), with exact steps for the user.

Rate severity honestly; state confidence per finding. Be ready to "show the exact code that proves this" for any finding.

**Then STOP and wait for the user's go-ahead.** After approval, fix findings in severity order, one at a time, updating the status column.

**Done when**
- [ ] `SECURITY_REVIEW.md` exists with a ranked findings table.
- [ ] Every Critical and High finding is fixed or has a clear owner and date.
- [ ] "Couldn't verify" items have been checked manually by the user.

Re-run after big features and before every major launch.

---

## 27 · Test the protections and write the report · VERIFY

Goal: every fix proven by an automated test that tries to break it; one trustworthy report.

**Rules**
- Run only against localhost or staging. Never destructive tests against production; never real customer data. Dedicated test accounts: signed-out visitor, user A, user B, admin.
- Real, repeatable tests in the project's existing framework (Vitest/Jest + supertest, Playwright, pytest + httpx…). If none exists, create a minimal setup and explain how to run it.
- Keep the tests in the repo; recommend CI on every push.

**Step 1 · "Try to break it" tests** for every protection that applies:
| # | Test |
|---|---|
| 01 | Every protected endpoint returns 401 when signed out |
| 03 | User A can't read/update/delete user B's resources (403/404); public key alone reads nothing private |
| 04 | HTTP redirects to HTTPS; HSTS present (staging/prod URL only) |
| 05 | Stored hashes use Argon2id/bcrypt/scrypt; no password in logs or responses |
| 06 | Negative/oversized/wrong-type/extra-field inputs rejected; `"role":"admin"` ignored |
| 07 | XSS payloads render as text |
| 08 | A failed login produces a log event without secrets |
| 09 | Normal user gets 403 on every admin page and endpoint |
| 10 | Injection payloads return normal empty/400 responses |
| 02/11 | Production build contains no secret patterns |
| 12 | The N+1th request returns 429 |
| 13 | Unknown origin gets no Allow-Origin header |
| 14 | All required security headers present |
| 15 | Session cookies have HttpOnly, Secure, SameSite; logged-out session rejected |
| 16 | State-changing request with foreign Origin / no token rejected |
| 17 | Used, expired and superseded tokens fail; real and fake emails get identical responses |
| 18 | Disguised HTML, script SVG, oversized file and `../` filename rejected |
| 19 | Tampered price, negative quantity, reused coupon, success URL without payment, unsigned or duplicate webhook all fail safely |
| 20 | Error responses contain no stack traces, paths or queries |
| 23 | Sensitive paths return 404 |
| 25 | Old keys rejected (give the user the commands to run manually if needed) |
| H2 | Authorization matrix: every role × endpoint × own/other-tenant resource returns the expected status |
| H5 | Forced dependency failures (auth provider down, DB timeout, payment API error) deny access and leave consistent state |
| H6 | Parallel requests can't double-spend credits, coupons or stock; replayed idempotency keys don't duplicate |
| H7 | Oversized page size, deep JSON and huge bodies are rejected; slow queries time out |
| P1 | Mobile: no secrets in the built bundle (`find-secrets.sh` on the unpacked IPA/APK/JS bundle); tokens only in Keychain/Keystore |
| P4 | AI: injection prompts in user content/documents can't trigger tools beyond the user's rights or leak other users' data |
| S1/S3 | Store apps: a forged "purchase succeeded" from the client unlocks nothing; account deletion removes data and revokes sessions |
| live | `scripts/check-headers.sh` and `scripts/check-exposed.sh` pass on staging/production |
| scan | `scripts/security_scan.py .` reports 0 ERROR; every WARN fixed or explained in the report |

**Step 2 · Fix and re-test:** for every failing test, explain the cause, apply the smallest correct fix, re-run until it passes. Never weaken or delete a test to make it pass.

**Step 3 · Write `SECURITY_REPORT.md`:**
1. Summary: total checks, Passed, Fixed & re-tested, Still open, Not applicable.
2. Table of ALL 27 checks: `# · check · status (Passed / Fixed & re-tested / Open – next step / Needs my action / N/A) · evidence (test name or command) · notes`. Then the same table for every applicable B1–B7, H1–H16, P1–P5 and S1–S10 check, under a heading with the ASVS level from SKILL.md §0.
3. Findings and fixes: what was wrong, files changed, the test that now proves it.
4. Open items with risk level and exact next step.
5. Manual actions only the user can do (dashboard settings, key rotation, MFA, billing caps) as a checklist.
6. How to run the security tests; recommendation to run them in CI on every push.

**Done when**
- [ ] Automated tests exist for every protection that applies.
- [ ] All tests pass, or each failure is listed as an open item.
- [ ] `SECURITY_REPORT.md` summarizes findings, fixes and open items.
- [ ] Security tests run in CI on every push.

Green tests ≠ perfectly secure; they prove what they test. Re-run check 26 as the app grows.

The 27 checks, for the report table: 01 Authentication · 02 Hide API keys · 03 Secure database · 04 HTTPS · 05 Hash passwords · 06 Server-side validation · 07 XSS · 08 Logging & monitoring · 09 Admin routes · 10 Parameterized queries · 11 Environment variables · 12 Rate limiting · 13 CORS · 14 Security headers · 15 Session cookies · 16 CSRF · 17 Reset links expire · 18 File uploads · 19 Prices & payments · 20 Debug mode off · 21 Vulnerable dependencies · 22 Unused packages · 23 Exposed files · 24 Git history secrets · 25 Rotate compromised keys · 26 Full security review · 27 Test & report.

---

## After launch: maintenance rhythm

| When | What |
|---|---|
| Every commit | Pre-commit secret scan runs automatically (24) |
| Every push / deploy | Security tests in CI (27); re-run `check-exposed.sh` after big deploys (23) |
| Weekly | Review Dependabot/Renovate PRs and security alerts; glance at failed-login and 5xx alerts |
| Monthly | Dependency audit (21), remove unused packages (22), review admin users and team access (B4), check billing dashboards (B5) |
| Quarterly | Full review (26) and test run (27); test a backup restore (B3); rotate high-value keys |
| Every big feature | Run the checks from SKILL.md §3 before shipping |
