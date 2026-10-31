# Discovery: asking the right questions, cutting scope

## 1. The questions that change what gets built

Ask at most 7, in one message, in plain language, each with a suggested default so the user can answer "ok". Skip any the user already answered or the material already shows.

1. **Who is it for and what pain does it remove?** (default: inferred from the request, stated back in one line)
2. **What is the one thing a user must be able to do on day one?** This becomes Slice 1.
3. **Who sees what?** Accounts or not, roles, is data private per user, per team, or public. (default: private per user)
4. **Platforms and languages.** Web, iOS, Android, desktop; Arabic, English, RTL. (default: responsive web, Arabic + English)
5. **Money.** Free, one-off, subscription, in-app purchase, marketplace fees. (default: none in MVP)
6. **Sensitive data or rules.** Payments, health, children, location, legal/regulatory region. Sets the ASVS level.
7. **Constraints.** Deadline, budget, existing stack or accounts (Supabase, Vercel, Firebase, Stripe), brand assets.

Never ask about things you can decide well yourself (folder structure, library choice, colour of a button). Decide, write it under Assumptions.

## 2. Reading what the user gives you

- **A competitor link or screenshot**: list its core jobs, then mark which ones the MVP needs. Never copy a product; take the job, not the design.
- **A voice note or long message**: extract nouns (entities), verbs (actions/stories), adjectives (non-functional targets), names (roles).
- **An existing repo**: map what already exists first (routes, tables, roles). Spec the delta, not the whole world.

## 3. Turning vague words into targets

| They say | Write |
|----------|-------|
| fast | p95 server < 300 ms; LCP < 2.5 s on mid-range mobile |
| secure | ASVS L2; launch-security checks 01–27 pass |
| easy / simple | main flow ≤ N steps; no manual required; first value in < 2 min |
| modern / beautiful | design-system direction chosen + craft floor passes (design-system skill) |
| scalable | target load numbers: users, requests/min, data size in 12 months |
| works offline | which actions work offline, how conflicts resolve |
| like X | the 3 jobs from X we keep, and what we do differently |

## 4. Scope-cutting techniques

- **One persona first.** Ship for the primary user; others go to Later.
- **Manual before automatic.** An admin doing a step by hand beats building a workflow engine for 10 customers.
- **Buy, don't build.** Auth, payments, email, search, analytics, file storage: use a provider (see `stack-picker`).
- **Walking skeleton first.** Prove deploy, auth, data and one screen end to end before any second feature.
- **Kill "and also".** Every "and also" goes to Later unless it blocks Slice 1.
- **Never list.** Write what the product refuses to be. It protects focus and stops the AI from inventing features.

## 5. When to stop discovering

Stop when you can write: the problem line, the Must column, acceptance criteria for each Must story, and the ASVS level. Everything else can be an assumption. Over-long discovery is its own failure: ship Slice 0 and learn.
