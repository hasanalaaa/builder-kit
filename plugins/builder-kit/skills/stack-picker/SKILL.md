---
name: stack-picker
description: Choose the technology stack, hosting, database, auth, payments, email, storage and AI providers for a new app, site, API, mobile or desktop project - boring, proven, AI-friendly defaults with the reasoning written down as an ADR. Use when starting a project, when the user asks "what should I build this with", compares frameworks or providers (Next.js vs Astro, Supabase vs Firebase, Expo vs Flutter vs native, Tauri vs Electron, Vercel vs Cloudflare), or plans a migration. Also for اختيار التقنية, أي إطار عمل, أي استضافة, ستاك المشروع.
---

# Stack Picker

The right stack is the most boring one that fully meets the spec. Boring means: widely used, well documented, typed, with a large body of public code, so humans and AI agents both write it correctly. Novel stacks cost you in every prompt, every bug and every hire.

| File | Use it for |
|------|-----------|
| `references/stacks.md` | Default stacks per project type, provider choices (DB, auth, hosting, payments, email, storage, AI, analytics), the decision table, migration notes |

## 1. Rules

1. **Spec first.** Read `SPEC.md` (or run `product-spec`). The stack follows from platforms, languages, data sensitivity, realtime/offline needs, budget and team skills, never from fashion.
2. **Prefer what already exists.** An existing repo, existing accounts (Supabase, Vercel, Firebase, Stripe) or a team's known language beat a theoretically better option. Switching has a cost; name it.
3. **One language end to end when possible.** TypeScript across web front end, API and mobile (Expo) cuts context switches for humans and AI.
4. **Buy the commodity, build the core.** Auth, payments, email delivery, file storage, error tracking, analytics: managed providers. Your code is for what makes the product different.
5. **Typed and validated at every boundary.** TypeScript `strict`, Python type hints + pydantic, a schema validator for input (Zod/Valibot/pydantic).
6. **Avoid lock-in where it is expensive.** Standard Postgres over proprietary data stores for core data; standard auth (OIDC/JWT) over bespoke; your domain on your DNS. Lock-in at the edges (email provider, error tracker) is cheap and fine.
7. **Check versions live.** Never pin a version from memory. Use the current stable/LTS from official docs or the package registry at setup time, and record it.
8. **Data region and law.** If users are in a regulated region, choose providers with a matching region and a DPA. Note it in the ADR.
9. **Cost ceiling.** Estimate monthly cost at launch and at 10× users. Set provider spend caps (see `launch-security` B5).

## 2. Workflow

1. Extract from the spec: surfaces (web / iOS / Android / desktop / API / extension), content vs app (static marketing vs logged-in product), realtime, offline, SEO need, data sensitivity (ASVS level), expected load, AI features, payments model (web Stripe vs store IAP), languages/RTL, team skills, budget.
2. Start from the default in `stacks.md` §1 for the project type.
3. Change a default only for a reason from step 1. Each change is one line: "X instead of Y because Z".
4. Pick providers from `stacks.md` §2.
5. Write `docs/adr/0001-stack.md` (format: `project-architecture/references/templates.md`): context, decision table, rejected options with one-line reasons, cost estimate, exit plan for each provider.
6. Record exact versions and the install/run/test/lint/build commands in the project `CLAUDE.md` (global CLAUDE.md §10).
7. Hand off to `project-architecture` NEW (layout for the chosen stack is in its `layouts.md`).

## 3. Red flags

- A new framework chosen because it is trending, with no spec reason.
- Two frameworks doing one job (React + Vue, Prisma + Drizzle, two state libraries, two CSS systems).
- A self-hosted database, auth server or email server for an MVP.
- Business logic in a proprietary low-code backend with no export path.
- Mobile app as a web view wrapper when the store rules or UX need native features (see `mobile-release`).
- Client-only app talking to the database with a public key and no row-level security (see `launch-security` 03).
- Microservices, Kubernetes, event buses or a separate API for an MVP with one team.

## 4. Done when

- [ ] ADR exists with decision table, rejected options, cost at launch and at 10×, exit plan per provider.
- [ ] Versions and commands recorded in the project `CLAUDE.md`.
- [ ] Every Must story in the spec is buildable with the chosen stack, with no "we'll figure it out" item.
- [ ] Region, compliance and spend caps noted.
