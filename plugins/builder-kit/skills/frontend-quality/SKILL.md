---
name: frontend-quality
description: Front-end engineering quality for React, Next.js, Vue/Nuxt, Svelte, Astro and React Native - where state lives, data fetching and caching, server vs client components, forms with schema validation, routing and URL state, component design and composition, rendering performance, TypeScript strictness, environment/config, and the defects AI tools leave in UI code (effects that sync derived state, fetch-in-useEffect, index keys, any/ts-ignore, giant client components, leftover console.log, raw img in Next.js). Use when building or reviewing UI code, components, hooks, pages, forms, state management, or when the UI is buggy, janky, re-renders too much or is hard to change. Also كود الواجهة, الفرونت, رياكت, المكونات. Ships fe_check.py.
---

# Front-end Quality

Design (`design-system`) decides what the UI looks like. This skill decides how the UI code is built so it stays correct, fast and changeable: state in one place, data fetched once and cached, forms validated by the same schema as the server, components small and composable.

| File | Use it for |
|------|-----------|
| `references/patterns.md` | State placement, data fetching (RSC, loaders, TanStack Query), server/client boundary, forms, URL state, component design, rendering performance, TypeScript, styling, env/config, React Native notes, Vue/Svelte notes, anti-patterns with fixes |
| `scripts/fe_check.py` | Scan for derived state in effects, fetch in `useEffect`, index keys, `any` / `@ts-ignore`, `console.log`, `"use client"` on pages/layouts, raw `<img>` in Next.js, inline component definitions, prop drilling depth hints, missing `key` in maps |

## 1. Rules

1. **State has one owner.** Server data → the server/cache layer (RSC, loader, TanStack Query/SWR). URL-worthy state (filters, tabs, page, search) → the URL. Form state → the form library. Shared client UI state → context or a small store. Local UI state → `useState`. Never copy one into another "to keep in sync".
2. **Derive, don't sync.** If a value can be computed from props/state, compute it during render (`useMemo` only if expensive). `useEffect` + `setState` to mirror data is a bug factory.
3. **Effects are for synchronizing with the outside world** (subscriptions, DOM APIs, non-React widgets). Not for data fetching in frameworks that have loaders/RSC, not for responding to events (put that in the handler).
4. **Server first** (Next.js App Router, Remix, Nuxt, SvelteKit, Astro): fetch on the server, keep components server-side by default, add `"use client"` to the smallest interactive leaf.
5. **One schema per form**, shared with the server (Zod/Valibot/pydantic), with React Hook Form / TanStack Form / native forms + server actions. Field errors from the server map back to fields.
6. **Components are small, named for what they are, and composable** (children/slots over 15 boolean props). Containers fetch; presentational components render props. Follow the project's feature folders (`project-architecture`).
7. **TypeScript strict, no `any`, no `@ts-ignore`** without a comment explaining why; types from schemas and generated API clients, not hand-written duplicates.
8. **Every async UI has loading, error, empty and success states** (`design-system/references/components.md` §0, `error-handling`).
9. **Performance by default**: images optimized and sized, code split per route, lists virtualized when long, no needless re-renders of large trees (`performance`).
10. **Accessible markup**: semantic elements, labels, focus management on route/dialog changes (`accessibility`).

## 2. Workflow: building a screen

1. Read `DESIGN.md` and the nearest sibling screen; reuse its data-fetching and component patterns.
2. Decide state placement (§1 rule 1) and write it down in the PR description in one line per piece of state.
3. Data: server component/loader or query hook with a typed client; define loading/error/empty UI.
4. Interactions: handlers do the work; mutations invalidate/revalidate the right cache keys; optimistic UI only with rollback.
5. Forms: schema → form → server action/endpoint → field errors.
6. Run `python3 <skill>/scripts/fe_check.py .`, `design_lint.py`, typecheck, tests.

## 3. Done when

- [ ] `fe_check.py` 0 ERROR; typecheck and lint clean.
- [ ] No derived state in effects; no fetch-in-effect where the framework has a data layer.
- [ ] URL reflects shareable state; back/forward work.
- [ ] Forms validated client + server with the same schema; server errors shown on fields.
- [ ] Loading/error/empty states exist; no layout shift when data arrives.
- [ ] `"use client"` only on interactive leaves; bundle impact checked for new dependencies.
