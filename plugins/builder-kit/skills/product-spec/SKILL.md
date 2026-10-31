---
name: product-spec
description: Turn an idea, a vague request or a feature ask into a build-ready spec before any code is written - problem, users, MVP scope, user stories with testable acceptance criteria, flows, data, non-functional targets, risks and vertical slices an AI agent can build one at a time. Use when starting a new app, site or feature, when the request is vague ("build me an app like…", "add a dashboard"), when scope keeps growing, or when the user says spec, PRD, requirements, MVP, user stories, scope, plan the app, فكرة تطبيق, متطلبات, مواصفات, نطاق المشروع, خطة الميزة. Produces SPEC.md (or a feature spec) that the other builder-kit skills build from.
---

# Product Spec

Most failed vibe-coded apps fail before the first line of code: the request was vague, the AI filled the gaps with guesses, and every later prompt fought the guesses. A spec removes the guessing. It is short, concrete and testable, and it is the contract every later step is checked against.

Two modes:
- **APP**: a new product. Write `SPEC.md` at the repo root (§2).
- **FEATURE**: a change to an existing product. Write a feature spec in `docs/specs/<feature>.md` (§3). Small changes (one screen, one endpoint, under a day) get the 10-line mini spec in §3 only.

| File | Use it for |
|------|-----------|
| `references/templates.md` | `SPEC.md` template, feature spec, mini spec, user story and acceptance-criteria formats, a filled example |
| `references/discovery.md` | The interview: which questions matter, how to ask them, how to fill gaps with explicit defaults, scope-cutting techniques |

## 1. Rules

1. **Problem before product.** One sentence: who has what pain, and how they cope today. If you can't write it, ask before building anything.
2. **Ask little, decide openly.** Ask only questions whose answers change what gets built (see `discovery.md`). Everything else gets an explicit default written in the spec under **Assumptions**, so the user can veto it in one glance.
3. **Every requirement is testable.** "Fast", "easy", "secure", "modern" are not requirements. "Search returns in < 300 ms for 10k items", "sign-up in ≤ 3 steps", "ASVS L2" are.
4. **Scope has three columns.** Must (MVP), Later, Never. "Never" is as important as "Must": it is what stops scope creep and AI over-building.
5. **Slice vertically.** Each slice is a thin, end-to-end, demoable piece (UI + API + data + test) that lands working. Never "all the database first, then all the API".
6. **One source of truth.** The spec lives in the repo, is updated when decisions change, and every later skill reads it. A decision made in chat that isn't in the spec didn't happen.
7. **Non-functional targets are part of the spec**: security level, accessibility level, languages and RTL, performance budget, platforms, data residency, cost ceiling.

## 2. APP workflow

1. **Discover** (`discovery.md` §1). Read whatever exists (notes, screenshots, competitor links, an existing repo). Ask the ≤ 7 questions that matter, in one message. If the user wants speed, skip asking and write defaults.
2. **Write `SPEC.md`** from `templates.md` §1:
   - Problem, target users and their main job-to-be-done.
   - Success metrics (how we know it works after launch).
   - Scope table: Must / Later / Never.
   - User stories for every Must item, each with Given/When/Then acceptance criteria, including the unhappy paths (empty, invalid, unauthorized, offline, failure of a third party).
   - Main flows as numbered steps, with the step count. Fewer steps wins (see `project-architecture` law 11).
   - Data: the entities, their key fields, ownership (who can see/change each), retention.
   - Roles and permissions matrix.
   - Non-functional targets (§1 rule 7).
   - Integrations (payments, email, AI, maps…), each with a fallback when it fails.
   - Risks and open questions.
   - Assumptions (every default you chose).
3. **Slice** into milestones: Slice 0 is the walking skeleton (deploys, one route, one table, CI green). Then one slice per user-visible capability, ordered by risk then value. Each slice lists its stories and its "done when".
4. **Review with the user**: show the scope table, the assumptions and the slice list only. Get a yes or edits. Update the file.
5. **Hand off**: `stack-picker` (if the stack isn't decided) → `project-architecture` NEW → `design-system` → build slice by slice, each slice following `ai-workflow`.

## 3. FEATURE workflow

1. Read `SPEC.md`, `ARCHITECTURE.md` and the code the feature touches.
2. Write the feature spec (`templates.md` §2): why, stories with acceptance criteria, UI states (loading, empty, error, success, no permission), data changes and migration, API changes, permissions, analytics events, rollout (flag or not), what it must not break.
3. Mini spec for small changes (`templates.md` §3): goal, acceptance criteria, files likely touched, out of scope.
4. Update `SPEC.md` scope table when the feature lands.

## 4. Quality bar for a spec

- [ ] A stranger (or a fresh AI session) can build the MVP from it without asking a question.
- [ ] Every Must item has acceptance criteria that a test can check, including at least one unhappy path.
- [ ] The Never list is not empty.
- [ ] Every assumption is written down.
- [ ] Each slice is demoable on its own and lists its done-when.
- [ ] Security level, a11y level, languages/RTL, performance budget and platforms are stated.
- [ ] Main flows show step counts; nothing takes more steps than it needs.
- [ ] It fits on a few screens. A spec nobody reads is not a spec.

## 5. Anti-patterns

- Feature lists without users or problems ("auth, dashboard, settings, notifications").
- Specs that describe the UI pixel by pixel but never the rules (who can do what, what happens on failure).
- "Phase 2" items silently built in phase 1 because the AI was on a roll.
- Acceptance criteria that only cover the happy path.
- A spec written once and never updated, so the code and the document disagree.
