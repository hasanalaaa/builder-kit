# Pipeline reference

## 1. Environments

| Env | Purpose | Data | Access |
|-----|---------|------|--------|
| Local | development | local DB (Docker / Supabase local), seed data | developer |
| Preview (per PR) | review a change in isolation | ephemeral or shared preview DB/branch (Neon/Supabase branching), fake data | team (password/SSO protected) |
| Staging (optional) | pre-production verification, integration with third-party test modes | production-like, anonymized | team |
| Production | users | real | users |

Parity: same runtime versions (`.nvmrc`/`engines`, `.python-version`), same build command, same database engine/version, same feature-flag system. Differences only through env vars.

## 2. Branching

Trunk-based: short-lived feature branches → PR → `main`. Release from `main`. Tags for versions (`v1.4.0`). Hotfix = small PR to `main` (never edit production by hand).

## 3. CI template (GitHub Actions, Node + pnpm example)

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }
permissions: { contents: read }
jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@<pinned-sha>        # pin actions by commit SHA
      - uses: pnpm/action-setup@<pinned-sha>
      - uses: actions/setup-node@<pinned-sha>
        with: { node-version-file: .nvmrc, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm typecheck
      - run: pnpm test -- --coverage
      - run: pnpm build
      - name: builder-kit scans
        run: |
          python3 "$BK/launch-security/scripts/security_scan.py" .
          python3 "$BK/project-architecture/scripts/arch_check.py" .
          python3 "$BK/error-handling/scripts/error_scan.py" .
        env: { BK: ./.builder-kit }   # vendored copy of the scripts, or skip in CI and run via ship-check locally
  e2e:
    needs: check
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<pinned-sha>
      - run: pnpm install --frozen-lockfile && pnpm exec playwright install --with-deps
      - run: pnpm exec playwright test
        env: { BASE_URL: ${{ steps.preview.outputs.url }} }   # from your host's preview deployment integration
```
Python variant: `actions/setup-python` with `python-version-file`, `uv sync --frozen` / `pip install -r requirements.txt`, `ruff check`, `mypy`/`pyright`, `pytest`.

Security of CI (`launch-security` H10): least-privilege `permissions`, pinned action SHAs, no secrets on `pull_request` from forks, OIDC to cloud instead of long-lived keys, Dependabot/Renovate for actions and deps.

## 4. Required checks and protections

- Branch protection on `main`: required status checks (check, e2e), at least one review (or self-review checklist for solo devs), linear history, no force pushes, no deletions.
- Dependency review / secret scanning / CodeQL where available.

## 5. Preview deployments

- Vercel/Netlify/Cloudflare Pages create one per PR automatically; Fly/Render have preview environments; for others, deploy a per-PR app with a TTL.
- Previews use preview env vars (test-mode Stripe keys, preview DB), are password-protected, `noindex`, and webhooks point to preview endpoints only if needed.
- Post the preview URL to the PR; E2E runs against it.

## 6. Secrets and env vars

- Store in host secret stores (Vercel/Netlify/Cloudflare env, Fly secrets, GitHub Actions secrets/environments, Doppler, 1Password, AWS/GCP secret managers).
- `.env.example` lists every variable name with a comment; startup validation fails fast on missing/invalid values.
- Never print env in CI logs; mask secrets; rotate on team changes (`launch-security` 25).
- Public (client-exposed) variables only with the framework prefix and only non-secret values.

## 7. Migrations in the deploy

- Step order: build → run migrations (once, with a lock) → deploy new code → health check → shift traffic.
- Tools: `supabase db push`/`migration up`, `drizzle-kit migrate`, `prisma migrate deploy`, `alembic upgrade head`, `python manage.py migrate`.
- Migrations must be compatible with both old and new code (expand/contract). Destructive "contract" migrations ship in a later release.
- Long backfills run as background jobs, not in the deploy step.
- Backup/PITR confirmed before risky migrations.

## 8. Zero-downtime and rollouts

- Serverless/edge hosts swap atomically; containers use rolling deploys with health checks and graceful shutdown (handle SIGTERM, finish in-flight requests).
- Feature flags (PostHog, GrowthBook, Unleash, LaunchDarkly, or a DB table): deploy dark, enable for internal users, then 5% → 25% → 100%; kill switch for risky features.
- Canary: route a small % of traffic to the new version (Cloudflare/Fly/K8s/Argo Rollouts) and compare error rates.
- Rollback: Vercel "Instant Rollback"/promote previous deployment, Netlify "Publish deploy", Fly `fly releases` + `fly deploy --image <previous>`, Docker tag previous image. Practice once.

## 9. Versioning and changelog

- Semantic versioning for APIs/packages/apps; date or build number is fine for web apps.
- Conventional commits + release-please/changesets to generate changelogs and tags.
- Expose version/commit in the health endpoint and error tracking (release tag).

## 10. Hosting notes

| Host | Notes |
|------|-------|
| Vercel | Best for Next.js; preview per PR; env per environment; watch function timeouts/regions (co-locate with DB); spend management |
| Cloudflare (Pages/Workers) | Edge runtime limits (Node APIs); great caching/CDN/WAF; R2, D1, Queues |
| Netlify | Static/Jamstack + functions; deploy previews |
| Fly.io | Containers near users; Postgres; volumes; machines autostop |
| Railway / Render | Simple containers, workers, cron, managed DBs |
| VPS (Hetzner, DO) | Docker Compose + Caddy (auto HTTPS); you own patching, backups, monitoring |
| Supabase | DB/auth/storage/functions; migrations via CLI; branching for previews |
| Expo EAS | Build/submit/update for mobile (`mobile-release`) |

## 11. Docker essentials

```dockerfile
FROM node:22-alpine AS deps          # pin a specific version/digest, never :latest
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
FROM deps AS build
COPY . .
RUN pnpm build
FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
USER node                             # never run as root
EXPOSE 3000
HEALTHCHECK CMD wget -qO- http://localhost:3000/api/health || exit 1
CMD ["node", "server.js"]
```
`.dockerignore` excludes `.git`, `node_modules`, `.env*`, tests, local data. Scan images (Trivy/Grype) in CI.

## 12. Domains, DNS, SSL

- Registrar lock + 2FA on registrar and DNS accounts (`launch-security` B4).
- Apex + www with one canonical (301 the other); HTTPS automatic via host or Caddy/Let's Encrypt; HSTS once stable.
- Email DNS (SPF/DKIM/DMARC) set before sending (`email-notifications`).
- Low TTL before migrations, raise after.

## 13. Launch-day checklist

- [ ] Production env vars set and validated; test-mode keys replaced by live keys (payments, email).
- [ ] Migrations applied; backups/PITR on; restore tested.
- [ ] Domain, HTTPS, redirects, headers; robots/sitemap correct (`seo-discoverability`).
- [ ] Error tracking, uptime monitor, alerts, dashboards live (`observability`).
- [ ] Rate limits and spend caps on (`launch-security` 12, B5).
- [ ] Legal pages and consent live (`legal-compliance`).
- [ ] `ship-check` passes (builder-kit command running every scanner).
- [ ] Rollback rehearsed; on-call person and incident card ready.
- [ ] Smoke test of main flows on production with a real account (and a real small payment, then refund).

## 14. After every deploy

Check health endpoint version, error rate, p95 latency, key conversions; read new error groups in Sentry; roll back on regression; write a short note in the changelog.
