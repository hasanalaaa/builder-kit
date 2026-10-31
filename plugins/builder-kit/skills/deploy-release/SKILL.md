---
name: deploy-release
description: Load when setting up CI/CD, environments, first deploy, rollback, or when production breaks after a deploy. GitHub Actions, previews, secrets, migrations in deploy, flags, rollouts, hosting/DNS. Triggers: deploy, pipeline, release, staging, النشر, رفع الموقع.
---

# Deploy and Release

A deploy should be boring: every push runs the same checks, every merge produces a preview, production updates in minutes, and any release can be rolled back in one step. Most "works locally, breaks in production" incidents come from environment drift, missing env vars, un-run migrations and untested builds.

| File | Use it for |
|------|-----------|
| `references/pipeline.md` | Environments and parity, branching, CI pipeline template (GitHub Actions), required checks, preview deployments, secrets/env, migrations in deploys, zero-downtime, feature flags, rollouts and rollback, versioning/changelog, hosting notes, Docker, domains/DNS/SSL, launch-day and post-deploy checklists |
| `scripts/release_check.py` | Check the repo is release-ready: CI exists and runs lint/typecheck/test/build, env vars used in code are listed in `.env.example` (and no real `.env` committed), lockfile present and single, Node/Python version pinned, Dockerfile hygiene, health endpoint, migrations step |

## 1. Rules

1. **Everything through CI.** No manual builds to production. The pipeline is code in the repo.
2. **Main is always deployable.** Short-lived branches, PRs with required checks, preview deployment per PR.
3. **Same artifact everywhere.** Build once, promote the same build/image through staging to production; config differs only by environment variables.
4. **Environments are isolated**: separate databases, keys, storage and webhooks for preview/staging/production. Previews never touch production data. Staging and previews are `noindex` and preferably access-protected.
5. **Env vars are validated at startup** (`launch-security` P1) and documented in `.env.example` (names, no values). Secrets live in the host's secret store, never in the repo or CI logs.
6. **Migrations are part of the deploy**, run once before the new code takes traffic, backward compatible with the running version (`data-design` expand/contract).
7. **Releases are reversible**: instant rollback to the previous build (hosting "promote previous"), feature flags for risky features, data migrations designed so rollback doesn't need a down-migration.
8. **Ship gradually** when risk is high: flags, percentage rollouts, canaries, internal users first.
9. **Watch after deploy**: error rate, latency, key business events for 30–60 minutes; alerts wired (`observability`).
10. **Mobile is different**: store review, staged rollouts, OTA updates within store rules, forced-update path (`mobile-release`).

## 2. Workflow: first setup

1. Pick hosting from `stack-picker`; create production + preview (+ staging if needed) environments with separate resources.
2. Add CI from `pipeline.md` §3: install → lint → typecheck → test → build → security/structure scans → E2E on preview.
3. Protect `main`: required checks, review, no force-push.
4. Configure env vars per environment; generate `.env.example`; startup validation.
5. Wire migrations into the deploy step; seed only non-production.
6. Domain, DNS, HTTPS, redirects (www/apex), security headers (`launch-security` 04, 14).
7. Health endpoint (`/api/health` → checks DB connectivity, returns version/commit).
8. Run `python3 <skill>/scripts/release_check.py .` → 0 ERROR.

## 3. Workflow: each release

1. PR green (all checks + preview reviewed) → merge.
2. Pipeline deploys to production (or staging → promote).
3. Migrations ran; health endpoint shows the new commit.
4. Watch dashboards; announce; update changelog.
5. If something breaks: roll back first, investigate second (`launch-security` incident card for security events).

## 4. Done when

- [ ] `release_check.py` 0 ERROR.
- [ ] CI runs lint, typecheck, tests, build, scans on every push/PR; `main` protected.
- [ ] Preview per PR; staging/preview isolated from production data and noindexed.
- [ ] `.env.example` complete; env validated at startup; secrets only in the secret store.
- [ ] Migrations automated and backward compatible; rollback path tested once.
- [ ] Health endpoint + post-deploy monitoring + alerts.
