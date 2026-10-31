# Spec templates

## 1. `SPEC.md` (new product)

```markdown
# <Product name>: Spec
Status: draft | agreed | building | live   ·   Owner: <name>   ·   Updated: <date>

## Problem
<Who> struggles with <pain> when <situation>. Today they <workaround>, which costs <time/money/risk>.

## Users
| User | Main job to be done | How often | Device / context |
|------|--------------------|-----------|------------------|

## Success metrics
- Activation: <e.g. 40% of sign-ups create their first X within 10 minutes>
- Retention / value: <e.g. weekly active creators>
- Guardrails: <e.g. p95 page load < 2.5 s, error rate < 1%, support tickets per 100 users>

## Scope
| Must (MVP) | Later | Never |
|------------|-------|-------|

## User stories
### S1 · <short title>
As a <user>, I want <capability>, so that <outcome>.
Acceptance criteria:
- Given <context>, when <action>, then <observable result>.
- Given <invalid / empty / unauthorized / offline / provider down>, when <action>, then <safe result + message>.
Out of scope: <…>

## Main flows
### F1 · <name> (N steps)
1. …
Shorter alternative considered: <…>

## Data
| Entity | Key fields | Owner (who reads / writes) | Sensitive? | Retention |
|--------|-----------|----------------------------|-----------|-----------|

## Roles and permissions
| Action | Visitor | User | Owner of resource | Admin |
|--------|---------|------|-------------------|-------|

## Non-functional targets
- Platforms: web (responsive) / iOS / Android / desktop
- Languages: ar (RTL) + en · default: <ar>
- Security: ASVS <L1/L2/L3> (see launch-security §0)
- Accessibility: WCAG 2.2 AA
- Performance: LCP < 2.5 s, INP < 200 ms, CLS < 0.1 on mid-range mobile; API p95 < <N> ms
- Availability / backups: <…>
- Data residency / compliance: <GDPR, local law, store rules>
- Budget: hosting <$/month>, AI spend cap <$/month>

## Integrations
| Service | Purpose | Failure behaviour (fallback) |
|---------|---------|------------------------------|

## Slices
| # | Slice | Stories | Done when |
|---|-------|---------|-----------|
| 0 | Walking skeleton | — | deployed to preview, CI green, one route reads one table, auth stub |
| 1 | … | S1, S2 | acceptance criteria pass as automated tests; demo recorded |

## Risks and open questions
- <risk> → <mitigation or spike>

## Assumptions
- <every default chosen without asking; user can veto>
```

## 2. Feature spec (`docs/specs/<feature>.md`)

```markdown
# Feature: <name>
Why: <problem or metric it moves>  ·  Spec link: SPEC.md#<section>

## Stories and acceptance criteria
(as in SPEC.md, happy + unhappy paths)

## UI states
| Screen / component | Loading | Empty | Error | Success | No permission | Offline |
|--------------------|---------|-------|-------|---------|---------------|---------|

## Changes
- Data: <tables/columns, migration, backfill, RLS/policies>
- API: <endpoints, request/response, errors, version impact>
- Permissions: <who can do what>
- Analytics events: <name · properties · why>
- Rollout: <feature flag? staged? kill switch?>

## Must not break
<existing flows, published contracts, performance budgets>

## Out of scope
<…>
```

## 3. Mini spec (small change)

```markdown
Goal: <one sentence>
Acceptance: <2–4 Given/When/Then lines, one unhappy path>
Touches: <files/modules likely changed>
Out of scope: <…>
```

## 4. Writing good acceptance criteria

- Observable from outside: a status code, a visible message, a row in the database, an email sent. Not "the code handles it".
- One behaviour per line. Numbers instead of adjectives ("within 2 s", "max 10 MB", "after 5 failed attempts").
- Always cover: empty input, invalid input, no permission, someone else's resource, duplicate submit, slow or failing third party, offline (mobile), the limit (max length, max count).
- Each criterion maps to one automated test (see `testing-strategy`).

Weak → strong:
- "Users can upload a photo" → "Given a signed-in user, when they upload a JPEG/PNG/WebP ≤ 10 MB, then it appears in their gallery within 5 s. Given a 12 MB file or a renamed .exe, then upload is refused with 'This file type or size isn't supported' and nothing is stored."
- "Fast search" → "Given 10k items, search results render in < 300 ms p95 on the server and show 'No results for <term>' when empty."

## 5. Filled example (short)

```markdown
# Rawdah: Spec
## Problem
Nursery owners track daily child updates on paper and WhatsApp; parents miss messages and staff waste ~40 min/day.
## Scope
| Must | Later | Never |
| Staff post a daily update (meal, nap, photo) per child | Billing | Public social feed |
| Parents see only their own child's updates | Attendance QR | Chat between parents |
| Owner manages staff and children | Multi-branch | Video streaming |
## S1 · Post a daily update
Given a staff member assigned to class A, when they post a meal update for child C in class A, then the parents of C see it within 10 s and get one push notification.
Given a staff member not assigned to C's class, when they try to post for C, then the API returns 403 and nothing is saved.
Given a photo > 10 MB, then it is refused with a clear message.
## Non-functional
Arabic first (RTL), English second · ASVS L2 (children's data → treat photos as sensitive, private storage, signed URLs) · WCAG 2.2 AA · iOS + Android via one codebase.
## Slices
0 skeleton · 1 auth + roles · 2 children & classes · 3 daily updates + photos · 4 push notifications
## Assumptions
One nursery per account in MVP · photos kept 12 months · Arabic default.
```
