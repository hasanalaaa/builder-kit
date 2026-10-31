---
name: project-architecture
description: Senior-engineer project structure for any app, site, API, mobile or desktop project - the "clean wiring" standard that stops AI-generated tangle. Use whenever starting a new project or scaffolding, adding a feature or file, deciding where code goes, creating a helper/util/component/hook/type, refactoring, or when the codebase feels messy, duplicated or hard to change. Also when the user says architecture, folder structure, project map, organize, clean up, spaghetti code, vibe-coded mess, هيكلة, تنظيم المشروع, خريطة المشروع, ترتيب الكود. Produces and maintains ARCHITECTURE.md, enforces module boundaries with tooling, and runs scripts/arch_check.py to catch duplication, cycles, god files and boundary leaks.
---

# Project Architecture

The goal: a codebase that looks like a professional electrical install. Every wire has its own labelled path. Every connection goes through a defined junction box. Anyone (a human or an AI agent) can open the panel, see the map, find where a thing lives, and know where a new thing goes.

The opposite is a pile of tangled cables. Research on AI-assisted code shows that tangle measurably: GitClear's analysis of hundreds of millions of changed lines found copy-pasted code rising sharply and refactoring ("moved" code) falling since AI assistants spread. The usual causes are context-blind generation: new helpers written next to existing ones, a third way of fetching data, logic dropped wherever the cursor was. This skill exists to prevent that.

Four modes. Pick by the request:
- **NEW**: starting a project. Follow §3.1.
- **BUILD**: any change to an existing project. Follow §3.2 on every change, however small.
- **UNTANGLE**: the project is already messy. Follow §3.3 and `references/refactoring.md`.
- **SIMPLIFY**: the code or the user flow works but is longer or harder than it needs to be ("make it shorter", "simplify", "fewer clicks", "اختصر"). Follow §3.4 and `references/simplify.md`.

| File | Use it for |
|------|-----------|
| `references/layouts.md` | Concrete folder layouts per stack: Next.js, React/Vite, Node APIs, NestJS, FastAPI, Django, Go, Expo/React Native, Flutter, SwiftUI, monorepos, Supabase/BaaS apps, static sites |
| `references/enforcement.md` | Turning the rules into tooling: formatters, linters, strict types, boundary rules (dependency-cruiser, eslint-plugin-boundaries, import-linter, Go `internal/`, Nx), dead-code and duplication finders, pre-commit, CI |
| `references/refactoring.md` | Untangling an existing mess safely, step by step, without a rewrite |
| `references/templates.md` | `ARCHITECTURE.md`, ADR, and the CLAUDE.md/AGENTS.md conventions block |
| `references/simplify.md` | Same capability with less code and fewer user steps: the shortening ladder, before/after code patterns, UX step reduction, the SIMPLIFY workflow and the equivalence checklist |
| `scripts/arch_check.py` | Architecture fitness check (stdlib Python, any repo): god files, long functions, too many parameters, deep nesting, import cycles, cross-feature leaks, duplicated blocks, junk-drawer and `_v2` files, commented-out code, crowded folders. `--stats` prints size metrics for before/after comparisons |

Talk to the user in their language (Arabic if they write Arabic). Code, paths and identifiers stay as-is.

---

## 1. The eleven laws (apply always)

1. **A true map exists.** `ARCHITECTURE.md` at the repo root (template in `references/templates.md`) shows the modules, what each owns, how they may depend on each other, and where new code goes. Read it before changing code. When a change alters the structure, update the map **in the same change**. A stale map is worse than none.
2. **Feature first, layer second.** The top level of `src/` describes what the app *does* (`billing/`, `orders/`, `auth/`), not what framework it uses (`controllers/`, `models/`, `services/` for everything). Each feature is a vertical slice that holds its own UI, logic, data access and tests.
3. **Every module has one front door.** Each feature/module exposes a public API (`index.ts`, `__init__.py`, a Go package's exported names). Other modules import only through that door. Everything else inside is private.
4. **Dependencies flow one way.** `app → features → shared`. A feature may use `shared/` and infrastructure adapters. `shared/` never imports a feature. Business logic never imports framework, HTTP or database code directly. **No import cycles, ever.** Features talk to each other through public APIs (or events), never by reaching into each other's internals.
5. **One home per concern.** Each cross-cutting thing has exactly one implementation, listed in the map's "Single source of truth" table: config/env loading, database client, data-access pattern, HTTP/API client, auth/session helpers, error types and error handling, logging, validation schemas and shared types, constants and enums, design tokens and UI primitives, translations. A second copy is a defect.
6. **Search before you create.** Before writing any function, component, hook, type, schema, constant or util, search the codebase for an existing one (by name, by behavior, by the strings it would contain). Reuse it, or extend it in its home. Never write a parallel version.
7. **Small, single-purpose units.** One file = one responsibility. Budgets: a file ≤ 300 lines (hard limit 500), a function ≤ 50 lines, ≤ 4 parameters (use an options object beyond that), nesting ≤ 3 levels. Split by responsibility, not by line count alone.
8. **Names tell the truth.** One naming convention per language, applied everywhere. Name things by domain meaning (`calculateOrderTotal`, not `processData`). Banned:
   - Junk drawers: `utils/`, `helpers/`, `misc/`, `common/`, `stuff/` that collect unrelated code. A small `shared/lib/` of focused, named modules (`shared/lib/money.ts`, `shared/lib/dates.ts`) is fine.
   - Versioned copies: `_v2`, `_new`, `_old`, `final`, `copy`, `backup`, `fixed` in file names. Change the original; Git is the archive.
   - Commented-out code and dead code. Delete it.
9. **No speculative machinery.** No abstraction until there are two real uses (or a real testing need). No interface with one implementation, no factory for one product, no config nobody asked for. Start with the simplest structure that keeps the laws, and grow it in layers as the app grows.
10. **Enforced by tools, not hope.** Formatter, linter, strict type checking, automated boundary rules, `arch_check.py`, and tests run on every commit and in CI (`references/enforcement.md`). A rule that isn't checked will erode.
11. **The shortest clear path.** For the same behavior, prefer the version with fewer concepts: fewer lines, fewer layers, fewer files, fewer steps for the user. Climb the shortening ladder before writing (`references/simplify.md` §1): delete → reuse → platform → framework built-in → installed library → data instead of code → generalize on the third copy → only then new code. Clear always beats clever: no code golf, nested ternaries or cryptic names, and never drop validation, security, error handling or accessibility to save lines.

---

## 2. The default architecture

### 2.1 Shape

A **modular monolith** made of **vertical feature slices**, with a thin app shell and a small shared kernel. It is the best default for almost every app: one deployable, clear boundaries, easy for humans and AI agents to navigate. Split into separate services only for a real, measured need (independent scaling, separate teams, different runtime), and record that decision in an ADR.

```
src/
  app/                  # the shell: entry point, routing, providers, dependency wiring (composition root)
  features/             # one folder per business capability
    orders/
      index.ts          # the front door: the ONLY file other modules import
      ui/               # screens/components for this feature (front end)
      api/              # transport: route handlers, controllers, server actions
      domain/           # pure business rules, types, validation schemas (no I/O)
      data/             # database queries / external calls for this feature
      orders.test.ts    # tests live next to the code they test
    billing/
    auth/
  shared/               # domain-free building blocks used by 2+ features
    ui/                 # design-system primitives (Button, Input, Modal)
    lib/                # focused generic modules (money.ts, dates.ts)
    config/             # typed, validated env/config (one place)
  infra/                # adapters to the outside world: db client, email, payments, queue, storage, AI SDK
```

Exact names vary by stack (Next.js `app/` is the router; Django calls features "apps"; Go uses `internal/`). Use the stack's conventions from `references/layouts.md`, keeping the same dependency rules.

**Scale the depth to the size.** A feature with three files doesn't need `ui/ api/ domain/ data/` folders. Start flat (`orders/OrderList.tsx`, `orders/orders.service.ts`, `orders/index.ts`), and add sub-folders when a feature passes roughly 8–10 files.

### 2.2 Who may import whom

```
app ──▶ features ──▶ shared
          │
          └──▶ infra (only from a feature's data/ layer, or through an interface the app wires in)

inside a feature:  ui / api ──▶ domain ◀── data
```

- `shared/` and `infra/` never import from `features/` or `app/`.
- A feature imports another feature only via that feature's `index`. If two features need each other in both directions, the shared concept is its own module, or one side emits events.
- `domain/` imports nothing with I/O: no framework, no DB, no fetch, no env. That makes business rules testable in milliseconds.

### 2.3 What each layer may do

| Layer | Does | Never does |
|-------|------|-----------|
| Transport (`api/`, handlers, server actions, controllers) | Authenticate, parse and validate input, call one use case, map the result to a response | Business rules, SQL, calling other features' internals |
| Use case / service | Orchestrate a business action: authorization, transactions, calls to domain + data | Know about HTTP, request/response objects, UI |
| Domain | Pure rules, calculations, state transitions, types, schemas | I/O of any kind |
| Data (`data/`, repositories) | Queries and external calls for its feature, returning plain typed data | Business decisions, formatting for UI |
| UI | Render state, handle user events, call hooks/queries | Inline fetch logic scattered in components, business rules, secrets |
| App shell | Routing, providers, composition (wiring implementations to interfaces), global error boundary | Feature logic |

Security fits the same map: auth helpers, input validation and error handling each live in one place and are called at the transport boundary (see the `launch-security` skill).

---

## 3. Workflows

### 3.1 NEW: starting a project

1. **Clarify** the product's core capabilities (these become the features), the stack, and where it runs. Ask only for what you can't decide sensibly; state assumptions.
2. **Pick the layout** for the stack from `references/layouts.md`.
3. **Write the map first:** `ARCHITECTURE.md` from the template, a conventions block in `CLAUDE.md` (and `AGENTS.md` if other agents are used), and `docs/adr/0001-stack-and-architecture.md`.
4. **Build a walking skeleton:** one real feature wired end to end through every layer (UI → transport → use case → domain → data → database), with its tests. This proves the wiring before anything is copied.
5. **Install the guard rails on day one** (`references/enforcement.md`): formatter, linter, strict types, boundary rules, test runner, pre-commit hook, CI running all of them plus `arch_check.py`.
6. Run `python3 scripts/arch_check.py <repo>` and fix every ERROR before adding the next feature.

### 3.2 BUILD: every change

**Before writing code**
1. Read `ARCHITECTURE.md` (create it via §3.3 step 1 if missing) and the files you'll change, their callers and tests.
2. Decide where the change lives:
   - It belongs to one feature → that feature's folder.
   - It's a new business capability → a new feature folder with its own `index`.
   - It's a domain concept several features need (e.g. `users`, `money`) → its own module with a public API. It doesn't go in `shared/`.
   - It's generic and domain-free (date formatting, a Button) and used by 2+ features → `shared/`.
   - It talks to an outside system → an adapter in `infra/`, called from a feature's `data/`.
   - It's app-wide wiring (routes, providers) → `app/`.
   - None fit, or two fit → stop, propose options to the user, and record the decision in an ADR.
3. **Search** for existing code that already does it (law 6). Look at how the nearest sibling feature solves the same problem and follow that pattern exactly. If the existing pattern is bad, say so and fix it everywhere in a separate step. Don't introduce a second pattern.

**While writing**
- Write the shortest clear version first (law 11). Before adding a state variable, effect, wrapper, flag, screen or click, ask whether the platform, the framework or a derived value already gives it.
- For UI work, count the user's steps to finish the task and cut any that don't add safety or clarity (`references/simplify.md` §3).
- Stay inside the change's home. Touch other modules only through their public API.
- Keep files and functions inside the budgets (law 7). Split when you'd cross them.
- Every new module gets its `index` front door and its tests next to it.

**After writing**
1. Run formatter, linter, type check, tests, boundary rules and `arch_check.py`. All green.
2. Re-read the diff as a reviewer against §4.
3. If the structure changed (new module, new dependency direction, moved code), update `ARCHITECTURE.md` in the same change. If a significant choice was made, add an ADR.

### 3.3 UNTANGLE: an existing messy project

Follow `references/refactoring.md`. In short:
1. **Map the current state honestly:** run `arch_check.py`, generate a dependency graph, find hotspots (files that change often AND are complex). Write the "as-is" map.
2. **Draw the target map** using §2, and agree it with the user.
3. **Put a safety net** under the critical flows (characterization tests) before moving anything.
4. **Move in small, shippable steps:** one move per commit, app working after each. Break cycles first, then pull duplicated code into its single home, then split god files, then move code into feature folders, then delete dead code. Never do a big-bang rewrite.
5. **Lock each improvement in** with a boundary rule or `arch_check` threshold so it can't regress.

### 3.4 SIMPLIFY: same capability, less code, fewer steps

Follow `references/simplify.md` §4. In short:
1. **Baseline:** tests green, `arch_check.py . --stats`, and steps-to-goal for the key user flows.
2. **Lock behavior** with characterization tests where coverage is thin.
3. **Rank candidates** (dead code, duplicates, pass-through layers, verbose patterns, extra UX steps) by what they remove versus the risk.
4. **One simplification per commit**, with tests, lint, types and `arch_check` green after each.
5. **Prove equivalence** with the checklist in `simplify.md` §5; revert anything you can't prove.
6. **Report before/after numbers** (lines, files, long functions, duplicates, steps-to-goal) and the tests that show behavior is unchanged.

---

## 4. The tangle checklist (review every diff against it)

These are the signatures of AI-generated mess. Any "yes" must be fixed before the change is done.

- [ ] **Duplicate:** does this add a function/component/type/constant that already exists elsewhere, even under another name?
- [ ] **Parallel pattern:** is this a second (or third) way of doing something the codebase already does (fetching, error handling, forms, state, styling, logging, config)?
- [ ] **Wrong home:** is code placed by convenience instead of by the §3.2 decision list (SQL in a component, business rules in a route handler, feature logic in `shared/`)?
- [ ] **Boundary leak:** does a module import another feature's internals, or does `shared/`/`infra/` import a feature?
- [ ] **Cycle:** does any import create a loop?
- [ ] **God file / god function:** does any file or function exceed the budgets, or do more than one job?
- [ ] **Junk drawer:** did something land in `utils/helpers/misc/common` because it had no clear home?
- [ ] **Versioned copy:** any `_v2`, `_new`, `_old`, `final`, `copy` file, or an old implementation kept "just in case"?
- [ ] **Dead weight:** commented-out code, unused exports, unused files, unused dependencies, leftover debug logs?
- [ ] **Speculative abstraction:** a layer, interface, factory, generic or config option with only one use?
- [ ] **Magic values:** repeated literal strings/numbers that belong in one constant or config?
- [ ] **Type drift:** the same shape redefined in several files instead of one schema/type imported everywhere?
- [ ] **Swallowed errors:** empty catches, or errors converted to `null` with no handling?
- [ ] **Noise comments:** comments that narrate what the code does instead of why?
- [ ] **Scope creep:** unrelated files reformatted, renamed or "improved" in the same change?
- [ ] **Longer than needed:** could the same behavior use fewer lines, layers, files or concepts (a built-in, a derived value, a lookup table, guard clauses, deleting an unused option)?
- [ ] **More steps than needed:** does the user click, type or wait more than the task requires?
- [ ] **Over-shortened:** did a "simplification" become cryptic or drop a check? Clear beats short.
- [ ] **Stale map:** structure changed but `ARCHITECTURE.md` didn't?

---

## 5. Definition of done (structure)

A change or a project is structurally done when:
- [ ] `ARCHITECTURE.md` matches reality (modules, dependencies, single-source-of-truth table).
- [ ] Formatter, linter, strict type check and tests pass.
- [ ] Boundary rules pass; `arch_check.py` reports **0 ERROR**; every WARN is fixed or explained.
- [ ] Every new module has a front door (`index`) and colocated tests.
- [ ] The code is the shortest clear version of the behavior, and user-facing flows have no avoidable steps.
- [ ] No item in the §4 tangle checklist is true.
- [ ] Significant decisions have an ADR.

Report results honestly: say what was verified (commands run, their output) and what wasn't.
