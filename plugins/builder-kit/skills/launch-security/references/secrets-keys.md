# Secrets & Keys: checks 02, 11, 24, 25

Apply SKILL.md §1 "Rules of work" and the "Finish every check with" table to every check here. Never print a secret value; show at most the first 4 characters.

---

## 02 · Hide API keys · CRITICAL

Goal: anything the browser (or a mobile bundle) can see, every visitor can see. Secret keys live only on the server.

**Self-check:** build for production, search the output (`dist/`, `build/`, `.next/static/`) for `sk_`, `sk-`, `secret`, `Bearer`, `api_key`, `service_role` (use `scripts/find-secrets.sh <build-dir>`). On the live site: DevTools → Sources → Cmd/Ctrl+Shift+F for the same words. DevTools → Network: do any request URLs/headers carry a key?

**Audit**
1. Search the whole codebase incl. config files for hard-coded keys/tokens: `sk_`, `sk-`, `pk_`, `AKIA`, `ghp_`, `xox`, `Bearer`, `api_key`, `apiKey`, `secret`, `token`, `password`, `service_role`, `private_key`, long random-looking strings.
2. List every third-party service: which key, called from client or server, and PUBLISHABLE or SECRET.
   - Usually publishable: Stripe `pk_`, Supabase anon/publishable key (only safe with RLS on), Firebase web config, domain-restricted Google Maps browser keys.
   - Always secret: Stripe `sk_`/`rk_`, OpenAI/Anthropic/any AI key, Supabase `service_role`/secret, database URLs, email/SMS provider keys, webhook secrets, JWT secrets, cloud credentials.
3. Every env var with a public prefix (`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`, `EXPO_PUBLIC_`, `PUBLIC_`, `NUXT_PUBLIC_`) holding a secret → flag.
4. Build for production and search the build output, to know what actually ships.

**Fix**
- Move every secret to server-only env vars.
- Replace each client call needing a secret with a server route/action/edge function that requires sign-in where appropriate, validates input, is rate-limited, and does only the one operation the UI needs. NEVER a generic proxy that forwards any URL/body (open relay).
- For publishable keys that stay public: tell the user which dashboard restrictions to add (allowed domains/referrers, allowed APIs, read-only scopes).

**Important:** removing a key from code does not un-leak it. Output a list of every secret that was EVER in client code or a public repo → rotation list for check 25.

**Watch out:** minified ≠ hidden. Mobile bundles (iOS/Android/Expo) can be extracted. Lovable/Bolt/v0 prototypes often put keys in front-end code.

**Done when**
- [ ] A search of the production build finds no secret keys.
- [ ] No secret uses a public env prefix.
- [ ] All third-party calls needing a secret go through your own server.
- [ ] Publishable keys have domain/scope restrictions in their dashboards.
- [ ] A list of keys to rotate exists.

---

## 11 · Environment variables · CRITICAL

Goal: clean split between public and server-only config; no `.env` in Git; separate dev and prod values.

**Self-check:** `git ls-files | grep -i env` → only `.env.example` (placeholders). Hosting dashboard env vars: any secret with a public prefix? Search code for fallbacks like `|| "secret"` or `?? "changeme"`.

**Audit**
1. Find every env var read (`process.env`, `import.meta.env`, `os.environ`, `Deno.env`, config files) and every `.env*` file. Table: `NAME · used client/server/both · public-safe or SECRET · notes` (names only).
2. Flag every SECRET with a public prefix or read in client code.
3. `.gitignore` covers `.env`, `.env.local`, `.env.*.local` etc. Is any `.env` tracked now, or ever in history?
4. Flag insecure fallbacks (`process.env.JWT_SECRET || "secret"`) and defaults that silently use test values in prod.
5. Secrets exposed via other routes: `/api/config`, `/api/health`, error messages, client logs, server-rendered page props, Docker images/build args, CI logs.
6. Dev and prod use separate values (Stripe test keys in dev, live only in prod; separate dev DB).

**Fix**
- Rename/move secrets so none are public; move secret-using code to the server.
- Add `.env.example` listing every variable with safe placeholders; update `.gitignore`.
- Startup validation (Zod schema, t3-env, pydantic-settings…) so the app fails fast with a clear message if a required var is missing, without printing values.
- Remove insecure fallbacks. Signing secrets are long random values (≥32 bytes); give the generate command (e.g. `openssl rand -base64 32`).

**Report:** every variable that may have been exposed (public prefix, committed file, logs) → rotation list for check 25.

**Watch out:** adding `.env` to `.gitignore` doesn't remove it from history (check 24). Env changes on most hosts need a redeploy.

**Done when**
- [ ] No secret has a public prefix or is read by client code.
- [ ] `.env` files are git-ignored; `.env.example` documents every variable.
- [ ] The app fails fast when a required variable is missing.
- [ ] Dev and production use different keys and databases.

---

## 24 · Scan Git history for leaked secrets · CRITICAL

Goal: a secret deleted in a later commit is still in history. Find every one ever committed and prevent new ones.

**Self-check:** `gitleaks git -v` (older: `gitleaks detect -v`) or `trufflehog git file://. --only-verified`. GitHub → Settings → Code security → enable Secret scanning and Push protection.

**Audit**
1. Scan FULL history, all branches and tags, with gitleaks or TruffleHog. If not installable, give the exact commands to run.
2. No scanner: search manually, e.g. `git log --all -p -S "<pattern>"` and `git log --all --full-history -- "**/.env*"`, for: `sk_live_`, `sk_test_`, `rk_live_`, `sk-`, `sk-ant-`, `AKIA`, `ghp_`, `github_pat_`, `xoxb-`, `xoxp-`, `AIza`, `-----BEGIN PRIVATE KEY-----`, `service_role`, `postgres://…:…@`, `mongodb+srv://…:…@`, `api_key=`, `secret=`, `password=`, long base64/hex in config files. Include every `.env` ever committed.
3. Report each: `type · file · commit hash · date · branch · still in current code?` Values masked (first 4 chars only).
4. Also check notebooks, test fixtures, CI config, Dockerfiles, docs and screenshots.

**Fix**
1. FIRST: every found secret goes on the check-25 rotation list. Rewriting history does NOT make a leaked key safe (forks, clones, caches).
2. Remove secrets still in current code; load from env vars.
3. Prevention: pre-commit hook running gitleaks (or pre-commit framework with a secrets hook), CI step scanning each push, instructions to enable GitHub secret scanning + push protection.
4. Only AFTER rotation and only if the user wants it: explain purging with `git filter-repo`, the impact (rewritten hashes, force-push, every collaborator re-clones), and how to ask GitHub to clear cached views for public repos. Force-push/history rewrite requires explicit user permission.

**Watch out:** rotate first, rewrite later (if at all). Private repos aren't safe storage.

**Done when**
- [ ] Full history (all branches) scanned.
- [ ] Every secret found is on the rotation list.
- [ ] No secrets remain in current code.
- [ ] Pre-commit scanning and GitHub push protection are on.

---

## 25 · Revoke and replace compromised keys · CRITICAL

Goal: any key ever exposed (front-end code, Git history, public file, logs, screenshot, shared chat, ticket) is treated as stolen: replaced, deployed, then revoked. The user does dashboard steps; you guide and update code/config.

**Self-check:** call each provider's API with the old key → 401/403. Check each provider's usage/billing for unrecognised activity during the exposure window.

**Step 1 · Inventory:** every credential: third-party API keys (AI, payments, email, SMS, maps), DB passwords/connection strings, Supabase service_role/secret, JWT/session signing secrets, OAuth client secrets, webhook signing secrets, cloud access keys/service-account files, deploy/CI tokens, SMTP creds. For each: where stored (host env per environment, CI, local `.env`, other services) and evidence of exposure (from checks 02, 11, 23, 24).

**Step 2 · Prioritise by blast radius:** payments and cloud/infra → database and service_role → AI and messaging (cost abuse) → the rest.

**Step 3 · Runbook per key, in this order:**
a) Where to create the new key (dashboard path), minimum scopes, restrictions (IPs/domains), spending limits.
b) Every place to update it (each host environment, CI secrets, local `.env`, other services/teammates).
c) Redeploy; confirm the app works with the new key.
d) Revoke/delete the old key.
e) Confirm the old key fails (safe, read-only test request).
f) Check provider logs/usage for misuse during exposure; say what to look for.
g) Side effects: rotating JWT/session secret logs everyone out (ask first); DB password rotation needs every connecting service updated; webhook secret rotation needs provider endpoint config updated.

**Step 4 · Harden:** code reads every credential from env vars, no fallback values; create `SECRETS.md` (name, purpose, owner, where stored, last rotated; NEVER values).

**Watch out:** deploy the new key BEFORE revoking the old one, or you cause your own outage. Exception (emergency): a leaked payment, cloud or AI key is revoked immediately even before the replacement ships; brief downtime is cheaper.

**Done when**
- [ ] Every exposed key replaced, deployed and revoked.
- [ ] Old keys confirmed dead (401/403).
- [ ] Provider logs checked for misuse.
- [ ] New keys have minimum scopes, restrictions and spending limits.
- [ ] `SECRETS.md` inventory exists (without values).
