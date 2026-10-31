# Deployment, Supply Chain & Monitoring: checks 08, 20, 21, 22, 23

Apply SKILL.md §1 "Rules of work" and the "Finish every check with" table to every check here.

---

## 08 · Log and monitor suspicious activity · MEDIUM

Goal: find out about attacks in minutes, without logs becoming a breach themselves.

**Self-check:** fail a login 5 times; can you find those events within 2 minutes, with time, account and IP? Would anyone be alerted? Search logs for `password`, `token`, `authorization` → must be redacted.

**Audit**
1. Current logging: what, where (console, Vercel/Netlify logs, Sentry, Datadog, Axiom, Better Stack…), retention, who can read it.
2. Any log line or error report containing passwords, tokens, session IDs, API keys, reset links, full card numbers, or full bodies with personal data.

**Fix**
1. Structured JSON security events through one helper, e.g. `logSecurityEvent(event, details)`. Events: login success/failure, logout, sign-up, password change, reset requested/completed, email change, MFA changes, permission denied (401/403), admin actions and role changes, rate-limit hits (429), payment and webhook events (incl. signature failures), file uploads, API key creation, unexpected 5xx.
2. Each event: UTC timestamp, event name, user ID (if known), IP, user agent, request ID, outcome. Expose the request ID in error responses so user reports match log lines.
3. Redact everywhere: passwords, tokens, cookies, Authorization headers, API keys, card data. Configure the error tracker to scrub them. Strip newlines from user values (log injection).
4. Alerts (or exact provider setup steps): >10 failed logins per account or IP in 5 min; spikes in 401/403/429/5xx; any new admin or role change; webhook signature failures.
5. Recommend retention; restrict log access to the user/team.

**Deliver:** one-page `SECURITY_RUNBOOK.md`: where logs are, how to search one user's activity, what each alert means, first three actions when one fires.

**Watch out:** log IDs, not full profiles (privacy). Serverless console logs vanish fast on some hosts; ship to a log service with retention.

**Done when**
- [ ] Security events logged with time, user, IP and request ID.
- [ ] No secrets or passwords in logs or error reports.
- [ ] Alerts exist for brute force, error spikes and admin changes.
- [ ] A short runbook exists.

---

## 20 · Disable production debug mode · HIGH

Goal: users see "something went wrong" + reference ID; details go privately to logs.

**Self-check (live site):** visit a missing page, send malformed JSON to an API, use an invalid ID → clean errors, no stack traces. Are `.map` files downloadable (DevTools → Sources)? Try `/docs`, `/redoc`, `/graphql`, `/swagger`.

**Audit**
1. Framework production debug settings:
   - Django: `DEBUG = False`, `ALLOWED_HOSTS` set. Flask: debug off (Werkzeug debugger = remote code execution). FastAPI: `debug=False`; `/docs`, `/redoc`, `/openapi.json` disabled or protected if API is private.
   - Node/Express: `NODE_ENV=production`; error handler never sends `err.stack` or internal `err.message`.
   - Next.js/Vite/React: production build deployed (not dev server); no detailed errors in API responses.
   - Laravel: `APP_DEBUG=false`. Rails: `consider_all_requests_local = false`. Spring: Actuator endpoints restricted.
   - GraphQL: introspection and playground/GraphiQL off in prod unless intentionally public.
2. Every error path: catch blocks returning `error.message` or raw DB errors, 404/500 pages, validation errors.
3. Public source maps, directory listing, verbose headers (`X-Powered-By`, versions), debug/test routes, health/status endpoints leaking versions/env/deps, client `console.log` of sensitive data.

**Fix**
- Debug off in production via environment config (can't be forgotten).
- Global error handler: generic message + request ID to users; full detail to server logs/error tracking (check 08).
- Map DB and third-party errors to generic messages.
- No public source maps (upload privately to the error tracker instead).
- Disable directory listing; remove debug-only routes and noisy console logs from prod.

**Verify:** curl commands triggering a 404, a 500 and a validation error on production showing no stack traces, paths, queries or versions.

**Watch out:** preview/staging deployments are often public with debug on; protect with password or platform auth. Returning `error.message` from a catch is a sneaky leak (DB errors include table/column names).

**Done when**
- [ ] Debug off in production via environment config.
- [ ] Errors show generic message + reference ID, never stack traces.
- [ ] API docs/GraphQL playgrounds off or protected in production.
- [ ] Source maps not publicly served.

---

## 21 · Update vulnerable dependencies · HIGH

Goal: no known published vulnerability in the app; every package is real (no "slopsquatting").

**Self-check:** `npm audit --omit=dev` (or `pnpm audit --prod`, `yarn npm audit`), `pip-audit`, or `osv-scanner`. GitHub → Security → Dependabot alerts (enable if off). Framework on a supported, patched version.

**Audit**
1. Run the stack's audit tool (npm/pnpm/yarn audit, pip-audit, bundle audit, cargo audit, composer audit, osv-scanner). If you can't run it, give the exact command.
2. Table: `package · installed · fixed version · severity · direct/transitive · prod or dev-only · purpose`.
3. Core framework and runtime (Node.js, Python, Next.js, React, Django…) on supported, patched versions.
4. Supply-chain sanity for every DIRECT dependency: exists on the official registry, is the well-known one (not a near-identical typo-squat), real repository, reasonable downloads, no suspicious recent owner change. Flag anything an AI may have invented or misnamed, and unexpected install scripts (`postinstall`).
5. Lockfile committed; CI installs from it (`npm ci`, `pnpm install --frozen-lockfile`, pip with hashes or a lock tool).

**Fix**
- Upgrade production Critical/High first with the smallest version bump containing the fix.
- Major upgrades: read the changelog, list breaking changes affecting this code, fix them.
- Vulnerable transitive deps: upgrade the parent or use overrides/resolutions; explain why.
- Never blindly run `npm audit fix --force`.
- Rebuild and run tests after each group of upgrades.
- Set up Dependabot or Renovate (grouped updates) and GitHub security alerts.

**Report:** what was upgraded; what remains with reasons ("no fix available", "dev-only, not shipped"); anything suspicious.

**Watch out:** check every AI-suggested package on npmjs.com / pypi.org before installing. Subscribe to framework security announcements.

**Done when**
- [ ] No Critical/High vulns in production deps (or each one explained).
- [ ] Framework on a supported, patched version.
- [ ] Every direct dependency is real and legitimate.
- [ ] Lockfile committed; Dependabot/Renovate enabled.
- [ ] App builds and tests pass after upgrades.

---

## 22 · Remove unused packages and code · MEDIUM

Goal: smaller attack surface: no abandoned packages, routes, files, scripts or keys.

**Self-check:** JS/TS: `npx knip` or `npx depcheck`. Python: `deptry .`. Skim the API routes folder: is every route recognised and used?

**Audit**
1. Unused dependencies (knip/depcheck/deptry or careful search). Double-check each candidate: dynamic imports, config usage (build tools, PostCSS, Tailwind, Babel, ESLint, test setup), CLI usage in package.json scripts, peer deps, type packages.
2. Dev-only packages listed as production deps (types, linters, test/build tools).
3. Dead code still deployed: unused API routes/server actions, pages of removed features, old webhooks, test/demo/seed routes, abandoned admin tools, unused files in `public/`.
4. Unused env vars, third-party scripts (old analytics, chat widgets), OAuth apps and API keys tied to removed features.

**Fix**
- Remove unused deps; move dev-only to devDependencies (or equivalent).
- Delete dead routes/pages/files. If unsure, list them for the user instead of deleting (deletion of files you didn't create needs user approval).
- Remove unused third-party scripts and env vars.
- Rebuild, run tests, start the app to confirm it works.

**Report:** table `item · type (package/route/file/script/env var/key) · evidence unused · action`. List keys/OAuth apps to revoke in dashboards.

**Watch out:** unused-dependency tools have false positives; always build and test after removing.

**Done when**
- [ ] No unused dependencies; dev tools in devDependencies.
- [ ] Dead routes, pages and test endpoints deleted.
- [ ] Unused third-party scripts and keys removed or revoked.
- [ ] App still builds and runs.

---

## 23 · Check for exposed files · CRITICAL

Goal: nothing private (env files, Git data, backups, DB dumps) is downloadable.

**Self-check:** run `scripts/check-exposed.sh https://YOURDOMAIN` (own domain only). Every path should be 404 (or 403). Inspect `public/`, `static/` and build output for anything not meant for the public.

**Audit**
1. Inspect `public/`, `static/`, `assets/`, build output (`dist/`, `build/`, `out/`, `.next/static`) and anything served directly. Flag: `.env` files and backups, `.git`, DB files/dumps (`.sql`, `.sqlite`, `.db`), archives (`.zip`, `.tar.gz`), logs, IDE folders (`.vscode`, `.idea`), `.DS_Store`, config files with internal details, private documents, fixtures with real data.
2. Server/host config: directory listing on? Rules that serve dotfiles?
3. `robots.txt` and `sitemap.xml` don't advertise private paths (robots.txt is public, not protection).
4. Cloud buckets (S3, R2, GCS, Supabase Storage, Firebase Storage): which are public; can contents be listed?
5. `.dockerignore` / `.vercelignore` etc. keep secrets out of images/deployments.

**Fix**
- Delete or move sensitive files out of public locations.
- Deny rules so dotfiles and backup/dump extensions always 404 (host config, nginx location rules, or middleware); disable directory listing.
- Buckets private unless they must be public; disable listing on public ones.
- Any exposed file with secrets → rotation list (check 25).

**Deliver:** a re-runnable `scripts/check-exposed.sh` in the project (copy from this skill's `scripts/check-exposed.sh`), run only against the user's own domain.

**Watch out:** re-run after every major deploy (new build steps can re-introduce files). If `.env` was ever publicly reachable, treat every key in it as compromised.

**Done when**
- [ ] Every sensitive path returns 404/403 on the live site.
- [ ] Public folders contain only public files.
- [ ] Directory listing off; buckets private or not listable.
- [ ] A re-runnable `check-exposed.sh` exists.
