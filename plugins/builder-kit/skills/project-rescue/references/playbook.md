# Rescue playbook

## 0. Intake

Access checklist: repo (with history), hosting (Vercel/Netlify/Replit/Lovable), database/BaaS (Supabase/Firebase), domain/DNS, payment provider, email provider, analytics/error tracking, app store consoles, `.env` values (via a secure channel, never chat).

Safety: database backup/export taken and verified; `git tag rescue-start`; read-only exploration first.

Five questions for the owner:
1. What must never break (the money flow, the core user action)?
2. What's broken or worrying right now?
3. How many users/customers, and is real personal or payment data involved?
4. Deadlines or launches coming?
5. Who else has access (freelancers, agencies, old team members)?

## 1. Top-10 rescue checks (manual, ~1 hour)

1. **Keys in the client**: search the built bundle and repo (`launch-security/scripts/find-secrets.sh`), especially service-role keys, Stripe secret keys, OpenAI keys in `VITE_`/`NEXT_PUBLIC_` vars.
2. **Database open to the world**: Supabase tables without RLS or with `using (true)`; Firebase rules in test mode (`allow read, write: if true`); try reading another user's rows with the anon key.
3. **Auth checks only in the UI**: call API routes/edge functions directly without a session; change IDs in URLs (IDOR).
4. **Admin by client flag**: roles stored in user-editable metadata or localStorage.
5. **Payments trusted from the client**: price from the browser, access granted on success URL, unsigned webhooks.
6. **Git history secrets**: `.env` ever committed? (`git log --all -- .env`); public repo?
7. **No backups / no migrations history**: schema changed by clicking in the dashboard.
8. **Deploy is manual or from a laptop**; no preview; no rollback.
9. **No error tracking**: production errors invisible.
10. **Core flow broken on mobile / in Arabic / with slow network**.

## 2. Stop the bleeding (order)

1. Rotate exposed keys; restrict new keys (scopes, domains); move secret use server-side.
2. Enable RLS / lock Firebase rules with owner-based policies; verify with anon and a second user.
3. Add server-side auth + ownership checks to every API/edge function.
4. Fix payment trust: server prices, verified webhooks, entitlements table (`payments-billing`).
5. Remove debug endpoints, test data in production, open admin pages.
6. Rate limit auth, AI and email endpoints; set provider spend caps.
Each fix: test (abuse test that failed before), deploy, verify live, note in the report.

## 3. Stabilize

- Reproducible local setup: README steps work from a clean clone; `.env.example`; lockfile; Node/Python version pinned.
- Schema into migrations: `supabase db pull`/`db diff` to capture the current schema as the baseline migration; from now on migrations only.
- CI with lint/typecheck/test/build; preview deploys; branch protection.
- Error tracking + uptime + basic dashboards (`observability`).
- Backups/PITR on and a restore test.

## 4. Safety net

- Characterization E2E tests for the core journeys as they work today (sign up, main action, payment, admin action).
- Integration tests for critical endpoints with abuse cases (401/403/404/400).
- Then refactors can't silently break behavior.

## 5. Untangle (common AI-tool output problems)

| Problem | Typical in | Fix |
|---------|-----------|-----|
| Giant page components (800+ lines) with fetching, state and UI mixed | Lovable, Bolt, v0 | Extract data hooks/server functions, presentational components, feature folders |
| Supabase calls scattered in components | Lovable | One data-access module per feature; types generated from the DB |
| Duplicate components/helpers (3 date formatters, 4 button styles) | all | Pick one, migrate callers, delete the rest (`arch_check.py` duplicates) |
| Unused files, dead routes, abandoned experiments | all | `knip`/`arch_check.py` orphans; delete after confirming |
| `any` everywhere, no strict mode | all | Turn on strict per folder; generate DB/API types |
| Inline styles and random colors | v0, Bolt | Extract tokens (`design-system` EXTRACT), replace in steps |
| Physical left/right CSS, English-only strings | all | `i18n-rtl` retrofit workflow |
| Edge functions with copy-pasted auth logic | Lovable/Supabase | Shared `requireUser` helper |
| Replit: secrets in code, single file servers | Replit | Secrets manager, split modules, proper deploy target |
| Firebase: client writes everything | FlutterFlow, Firebase apps | Rules + Cloud Functions for privileged writes |

Follow `project-architecture/references/refactoring.md`: map first, one move per commit, tests green after each.

## 6. Improve

Design system and polish (`design-system`), performance (`performance`), accessibility (`accessibility`), SEO (`seo-discoverability`), simplify flows (`project-architecture` SIMPLIFY), AI cost controls (`ai-features`).

## 7. Rewrite vs rescue

Rewrite only if most of these are true: the stack can't meet a hard requirement (platform, performance, compliance); the codebase is small (days, not months, to rebuild) and has few users; there are no tests and behavior is simple to re-specify; the owner accepts a parallel-run period. Even then: strangler pattern (new pieces behind the same URLs/APIs, migrate route by route), never a big-bang switch.

## 8. Owner communication

- Weekly (or per phase) short update: fixed, in progress, next, risks, decisions needed.
- Explain risk in business terms ("anyone could read all customer orders" not "RLS disabled").
- Get explicit approval for: deleting data/files, schema-breaking changes, provider changes, anything that costs money.

## 9. `RESCUE_REPORT.md` template

```markdown
# Rescue report: <app> · <date>

## Summary (≤ 5 lines, plain language)

## Scanner results (before → after)
| Scanner | Before (ERROR/WARN) | After |
|---------|---------------------|-------|
| security_scan | 7 / 23 | 0 / 4 |
| arch_check | … | … |
| error_scan | … | … |
| design_lint / a11y_lint / rtl_lint | … | … |
| audit_tests | … | … |
| release_check / obs_check / legal_check | … | … |

## Findings and status
| ID | Severity | Area | Finding | Fix | Status | Evidence (test/commit) |

## Actions the owner must take
- [ ] Rotate <key> in <dashboard> (done by us / needs owner login)
- [ ] Enable MFA on <accounts>

## Remaining roadmap (prioritized)

## How to run, test and deploy (link to README / CLAUDE.md)
```
