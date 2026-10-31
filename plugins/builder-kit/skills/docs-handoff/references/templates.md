# Documentation templates

## 1. README.md

```markdown
# <Product>
<One line: what it is and for whom.> · Live: <url> · Status: <beta/live>

## Quick start
Prerequisites: Node <version> (see .nvmrc), pnpm, Docker (for local Supabase), <others>
1. `git clone … && cd …`
2. `pnpm install`
3. `cp .env.example .env.local` and fill values (ask <owner> or see 1Password vault "<name>")
4. `pnpm db:start && pnpm db:reset` (local database with seed data)
5. `pnpm dev` → http://localhost:3000 (test login: see seed file)

## Commands
| Task | Command |
|------|---------|
| Dev server | `pnpm dev` |
| Tests | `pnpm test` · E2E `pnpm e2e` |
| Lint / typecheck | `pnpm lint` · `pnpm typecheck` |
| Build | `pnpm build` |
| DB migration | `pnpm db:migrate` · new: `pnpm db:new <name>` |
| All quality gates | builder-kit `ship-check` |

## Project map
See ARCHITECTURE.md. Product: SPEC.md. Design: DESIGN.md. Decisions: docs/adr/.

## Deploy
Push to `main` → CI → production (Vercel). Previews per PR. Rollback: docs/runbooks/rollback.md.

## Troubleshooting
- <common error> → <fix>
```

## 2. Project CLAUDE.md / AGENTS.md

Draft: `python3 <ai-workflow>/scripts/context_pack.py .`. Sections (global CLAUDE.md §10): Stack · Commands · Entry points and key directories · Published contracts · Known traps · Never touch · Standards (builder-kit skills, ship-check). Keep under ~60 lines.

## 3. Runbooks (`docs/runbooks/*.md`)

Each runbook: when to use · prerequisites/access · steps (copy-pasteable commands) · how to verify · how to undo · who to contact.

- **deploy.md**: normal release, migrations, verification, announcement.
- **rollback.md**: host-specific instant rollback, feature flag kill switches, DB considerations.
- **incident.md**: severity levels, first 15 minutes (mitigate, communicate), roles, status page, postmortem template (`observability` §13; security incidents → `launch-security` incident card).
- **restore.md**: restore DB from PITR/backup to a new instance, verify, switch; expected time.
- **rotate-keys.md**: per provider: where to rotate, where the key is used, deploy order, verify old key rejected (`launch-security` 25).
- **payments.md**: disputes, refunds, failed webhooks replay, reconciliation mismatch (`payments-billing`).
- **on-call.md** (if relevant): alert → runbook mapping.

## 4. Onboarding guide (`docs/onboarding.md`)

Day 1: access list, local setup (README), walkthrough of ARCHITECTURE.md, first small task. Week 1: main flows end to end, how to ship (branching, PR checklist, CI), where logs/errors/dashboards are, who owns what.

## 5. CHANGELOG.md

Keep a Changelog format (Added/Changed/Fixed/Removed/Security) per version or date; generated from conventional commits where possible (release-please/changesets). User-facing release notes separately in plain language (and Arabic when users are Arabic-speaking).

## 6. API docs

Generated OpenAPI → rendered (Scalar, Redoc, Swagger UI, Mintlify/Fern for public APIs); authentication guide, quick start with curl examples, error format, rate limits, versioning/deprecation policy, changelog, SDK links (`api-contracts`).

## 7. User help docs

Task-based articles ("How to send an invoice"), screenshots in both languages, search, contact path; in-app links to relevant articles; keep a "What's new" page.

## 8. Client handover package

```markdown
# Handover: <product> · <date>

## Ownership and accounts (transferred to client)
| Service | Purpose | Owner account | Plan/cost per month | Notes |
|---------|---------|---------------|---------------------|-------|
| GitHub org | code | client-org | free | admins: … |
| Vercel | hosting | client team | Pro $20 | domains attached |
| Supabase | DB/auth/storage | client org | Pro $25 | PITR on |
| Stripe | payments | client | fees | webhooks configured |
| Apple / Google developer | app stores | client | $99/yr / $25 | |
| Domain registrar / DNS | domain | client | … | registrar lock, 2FA |
| Email provider, Sentry, analytics, AI providers | … | … | … | spend caps |

## Credentials
All secrets rotated at handover and delivered via <password manager shared vault>. Old builder access removed (list).

## How it works
Links: README, ARCHITECTURE.md, SPEC.md, DESIGN.md, runbooks, recorded walkthrough.

## Known issues and roadmap
| Item | Severity | Suggested fix | Effort |

## Maintenance plan
Weekly / monthly / quarterly tasks (dependency updates, security review, backups test, cost review).

## Support terms
<warranty period, response times, how to request changes>
```

Handover checklist:
- [ ] Client owns every account (not the developer's personal accounts); billing on client's card.
- [ ] Developer access reduced to agreed level; personal tokens revoked.
- [ ] Secrets rotated after transfer; MFA on all admin accounts.
- [ ] Docs complete and verified by a clean-clone setup.
- [ ] Walkthrough recorded; questions answered in writing.
