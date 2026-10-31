# Layouts per stack

Every layout below keeps the same rules from SKILL.md §2: feature folders with one front door, one-way dependencies (`app → features → shared`, never back), one home per concern, tests next to code. Names change to match each framework's conventions; the wiring doesn't.

Pick the closest one, adapt names to the framework's current docs, and record the choice in `docs/adr/0001-stack-and-architecture.md`.

---

## Next.js (App Router), full-stack

```
src/
  app/                          # ROUTING ONLY: thin page/layout/route files that call into features
    (marketing)/page.tsx
    (app)/orders/page.tsx       # imports from @/features/orders
    api/webhooks/stripe/route.ts
    layout.tsx
  features/
    orders/
      index.ts                  # public: components, server actions, types others may use
      components/               # OrderList.tsx, OrderForm.tsx
      actions.ts                # 'use server' actions: auth + validate + call service
      service.ts                # use cases (server-only)
      queries.ts                # data access for orders (server-only)
      schema.ts                 # Zod schemas + inferred types (shared by client and server)
      orders.test.ts
  shared/
    ui/                         # design-system primitives
    lib/                        # focused generic modules
  server/                       # server-only infrastructure
    db.ts                       # the one DB client
    auth.ts                     # requireUser(), requireAdmin()
    env.ts                      # validated env (fails fast)
    logger.ts
```
Notes: keep `app/` files thin (fetch via the feature, render feature components). Mark server-only modules with `import 'server-only'`. Configure the `@/` alias to `src/`. Client components (`'use client'`) never import from `server/`.

---

## React SPA (Vite)

```
src/
  app/            # main.tsx, router, providers, global error boundary
  pages/          # route-level screens that compose features (thin)
  features/
    cart/
      index.ts
      components/
      hooks/      # useCart(), built on the shared API client/query library
      api.ts      # calls to the backend for this feature
      model.ts    # types, pure logic
  shared/
    ui/  lib/  api/client.ts  config/
```
For larger front ends, Feature-Sliced Design (`app → pages → widgets → features → entities → shared`, each layer importing only from layers below) is a well-documented, lint-enforceable variant.

---

## Node API (Express / Fastify / Hono)

```
src/
  app.ts                  # create server, register plugins, mount each feature's routes
  server.ts               # start/listen (separate from app.ts so tests can import the app)
  features/
    orders/
      index.ts            # exports the router/plugin
      orders.routes.ts    # transport: validate (Zod), call service, map response
      orders.service.ts   # use cases
      orders.repo.ts      # queries
      orders.schema.ts
      orders.test.ts
  shared/
    errors.ts  http/  lib/
  infra/
    db.ts  mailer.ts  queue.ts
  config/env.ts
```

## NestJS

Nest modules are already feature modules: one module per capability (`orders.module.ts`, controller, service, repository/entity, DTOs). Rules: a module exports only what others may use; no circular module imports (`forwardRef` is a smell, not a fix); cross-cutting concerns in a `core/` module imported once by `AppModule`.

---

## Python: FastAPI

```
app/
  main.py                 # create_app(): include each feature router, middleware, exception handlers
  core/                   # config.py (pydantic-settings), db.py, security.py, logging.py
  features/
    orders/
      __init__.py         # public API: router, service functions, schemas others may use
      router.py           # transport
      service.py          # use cases
      repository.py       # queries
      schemas.py          # Pydantic models
      models.py           # ORM models
      test_orders.py
tests/                    # cross-feature / integration tests
pyproject.toml            # ruff, mypy/pyright, import-linter config
```

## Python: Django

One Django app per business capability (`orders/`, `billing/`), each with `models.py`, `views.py` or `api.py`, `services.py` (business logic stays out of views and models' save()), `selectors.py` (read queries), `tests/`. Project settings split by environment, env read in one place. Apps don't import each other's models freely: go through the other app's `services`/`selectors`.

---

## Go

```
cmd/api/main.go          # wiring only
internal/
  orders/                # package = feature: handler.go, service.go, store.go, orders_test.go
  billing/
  platform/              # db, logging, config, http server helpers
go.mod
```
`internal/` makes packages unimportable from outside the module. Packages are named by what they provide, never `util` or `common`. Define interfaces where they're consumed, not where they're implemented.

---

## Mobile: Expo / React Native

```
app/                     # Expo Router routes (thin screens that render feature components)
src/
  features/
    profile/  index.ts  components/  hooks/  api.ts  model.ts
  shared/
    ui/  lib/  api/client.ts  storage/secure.ts   # tokens only via SecureStore
  config/
```

## Mobile: Flutter

```
lib/
  main.dart
  app/                    # app widget, router, DI setup
  features/
    orders/
      presentation/       # widgets, state (Bloc/Riverpod/etc. - pick ONE app-wide)
      domain/             # entities, pure logic
      data/               # repositories, API/DB sources
  core/                   # theme, network client, errors, utilities with clear names
test/                     # mirrors lib/
```

## iOS: SwiftUI

Group by feature (`Features/Orders/OrdersView.swift`, `OrdersViewModel.swift`, `OrdersService.swift`), plus `Core/` (networking, persistence, keychain) and `DesignSystem/`. For larger apps, split features into local Swift packages; package boundaries are compiler-enforced.

---

## Monorepo (pnpm workspaces + Turborepo or Nx)

```
apps/
  web/        # Next.js
  mobile/     # Expo
  api/        # backend (if separate)
packages/
  ui/         # shared design system
  domain/     # shared pure types/schemas/business rules
  config/     # shared tsconfig, eslint, prettier presets
```
Apps depend on packages; packages never depend on apps. Only extract a package when 2+ apps truly share it. Nx's module-boundary lint rule or dependency-cruiser enforces the direction.

---

## Supabase / Firebase (BaaS) apps

Same feature layout on the client, plus:
```
supabase/
  migrations/        # every schema + RLS change as a migration (never dashboard-only edits)
  functions/         # edge functions, one folder each, shared code in _shared/
  seed.sql
src/shared/api/supabase.ts   # the one client instance
```
Database rules (RLS) are part of the architecture: they live in migrations and are reviewed like code.

---

## Static / marketing site

`src/pages` (or `app/`), `src/components/sections/` (Hero, Pricing…), `src/components/ui/`, `src/content/` (copy, data, Markdown), `public/`. Content separate from layout components, so copy changes never touch code.
