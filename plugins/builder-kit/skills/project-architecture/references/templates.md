# Templates

Fill these in for the real project. Delete sections that don't apply; never leave placeholder text in a committed file.

---

## ARCHITECTURE.md

```markdown
# Architecture

## What this app does
<!-- 2–3 sentences: the product, its users, its core capabilities. -->

## Stack
<!-- Language, framework, database, hosting, key services. Link ADR-0001. -->

## Map
<!-- The real folder tree, two or three levels deep, one comment per line. -->
src/
  app/        # routing, providers, composition root
  features/
    orders/   # create, list, cancel orders
    billing/  # plans, checkout, invoices, Stripe webhooks
  shared/     # ui primitives, generic libs, config
  infra/      # db client, mailer, payments adapter

## Modules
| Module | Owns (data + behavior) | Public API (front door) | May depend on |
|--------|------------------------|-------------------------|---------------|
| orders | orders, order_items tables; order lifecycle | features/orders/index.ts | shared, infra/db, billing (index) |
| billing | subscriptions, invoices; Stripe | features/billing/index.ts | shared, infra/payments |

## Dependency rules
- app → features → shared. shared and infra never import features.
- Features import each other only through index files.
- domain/ folders do no I/O.
- Enforced by: <!-- dependency-cruiser / import-linter / arch_check.py in CI -->

## Single source of truth
| Concern | The one place |
|---------|---------------|
| Env / config | src/shared/config/env.ts |
| DB client | src/infra/db.ts |
| Auth helpers | src/server/auth.ts (requireUser, requireAdmin) |
| API client | src/shared/api/client.ts |
| Errors | src/shared/errors.ts |
| Logging | src/infra/logger.ts |
| Validation schemas | each feature's schema.ts |
| UI primitives / design tokens | src/shared/ui |

## How a request flows
<!-- One concrete example, e.g. "Create order": page → OrderForm → createOrder action (auth + Zod) → orders.service.create → orders.queries.insert → db. -->

## Where new code goes
- Belongs to one feature → that feature's folder.
- New business capability → new folder under features/ with an index.
- Domain concept used by several features → its own module, not shared/.
- Generic, domain-free, used by 2+ features → shared/.
- Talks to an outside system → infra/ adapter.
- Unsure → ask; record the decision as an ADR.

## Conventions
<!-- Naming, file naming, test naming, state management choice, styling approach, error handling pattern. -->

## Decisions
<!-- Links to docs/adr/*.md -->

## Commands
<!-- install / dev / test / lint / typecheck / build / arch check -->
```

---

## ADR (docs/adr/NNNN-title.md)

```markdown
# NNNN. <Decision title>

- Status: proposed | accepted | superseded by NNNN
- Date: YYYY-MM-DD

## Context
<!-- The problem and the forces at play. What must be true? -->

## Options considered
1. <option>: pros / cons
2. <option>: pros / cons

## Decision
<!-- What we chose and why, in a few sentences. -->

## Consequences
<!-- What gets easier, what gets harder, what we must now do (rules, tooling, migration). -->
```

Write an ADR for: stack choice, architecture style, state management, data access approach, auth provider, splitting a service out, adding a major dependency, any exception to the dependency rules.

---

## CLAUDE.md / AGENTS.md conventions block

Add to the project's AI rules file so every agent session follows the map:

```markdown
## Architecture rules (see ARCHITECTURE.md)
- Read ARCHITECTURE.md before changing code. Update it in the same change when structure changes.
- Code lives in its feature folder (src/features/<name>/). Other features import only through its index file.
- Dependencies flow app → features → shared. shared/ and infra/ never import features. No import cycles.
- Before creating any function, component, hook, type or constant: search for an existing one and reuse it.
- One home per concern (see the single-source-of-truth table). Never create a second API client, config loader, logger, error type or DB client.
- Follow the pattern of the nearest sibling feature. Don't introduce a new pattern without asking.
- Files ≤ 300 lines, functions ≤ 50 lines. No utils/helpers/misc dumping grounds. No _v2/_new/_old files. No commented-out code.
- Tests live next to the code they test.
- Before finishing: lint, typecheck, tests, boundary rules and `python3 scripts/arch_check.py .` must pass.
```
