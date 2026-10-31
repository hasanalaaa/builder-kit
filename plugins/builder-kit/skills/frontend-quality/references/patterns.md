# Front-end patterns

## 1. Where state lives

| State | Home | Example |
|-------|------|---------|
| Server data | RSC / route loader / TanStack Query / SWR | invoices list, current user |
| Shareable view state | URL (`searchParams`, route params) | filters, sort, tab, page, selected item, search query |
| Form state | form library or native form | draft values, field errors, dirty/touched |
| Global client UI | context (rarely changing) or Zustand/Jotai (frequently changing) | theme, sidebar collapsed, toasts |
| Local UI | `useState` / `useReducer` | open/closed, hover, step in a wizard |
| Persistent preferences | localStorage + store, or user settings on server | density, language |

URL state helpers: `nuqs` (Next.js), `useSearchParams` + router, TanStack Router search schemas.

## 2. Data fetching

**Next.js App Router**
- Fetch in server components (`async function Page()`); pass data down as props. Parallelize with `Promise.all`; stream slow parts with `<Suspense>`.
- Mutations: server actions or route handlers → `revalidatePath`/`revalidateTag`.
- Client-side live data (polling, infinite scroll): TanStack Query in a client leaf, hydrated from server data when possible.
- Never fetch your own route handlers from server components (call the function directly).

**SPA (Vite/React)**: TanStack Query for all server data: `queryKey` conventions per feature (`['invoices', filters]`), `staleTime` set deliberately, mutations with `onSuccess: invalidateQueries`. Router loaders (TanStack Router / React Router) to start fetching before render.

**Rules**: no waterfalls (fetch in parallel), no duplicate fetching of the same data in sibling components (share the query key), cancel on unmount (AbortSignal is built in), handle 401 globally (redirect to sign-in).

## 3. Server/client boundary (RSC)

- Default server. `"use client"` only where you need state, effects, browser APIs or event handlers.
- Pass server components as `children` into client components to keep them server-rendered.
- Never import server-only modules (DB, secrets) into client components: mark them with `import "server-only"`.
- Serialize only what the client needs (no full DB rows with internal fields).

## 4. Forms

```tsx
const schema = z.object({ email: z.string().email(), amount: z.coerce.number().int().positive() });
type Input = z.infer<typeof schema>;
const form = useForm<Input>({ resolver: zodResolver(schema), defaultValues: { email: "", amount: 1 } });
// submit → server action that re-validates with the same schema and returns { ok, fieldErrors }
```
- Same schema on server; server field errors mapped with `form.setError`.
- Submit button disabled while pending (`useFormStatus` / `isSubmitting`); idempotency for creates.
- Native validation attributes too (`required`, `type`, `min`) for no-JS resilience.
- `autocomplete`, `inputmode`, labels (`design-system` components.md §2).

## 5. Component design

- One component per file for anything reused; co-locate small private pieces.
- Props: data + callbacks; avoid boolean explosion (`<Button variant="primary" size="sm">` via `cva`, not `isPrimary isSmall isGhost`).
- Composition: `children`, slots (`<Card><Card.Header/>…`), render props only when needed.
- Container/presenter split: data hook (`useInvoices`) + pure view (`InvoiceTable`), so the view is testable and reusable.
- Don't define components inside other components (they remount every render).
- Keys: stable IDs from data, never array index for lists that change.
- Controlled vs uncontrolled: pick one per input; don't switch.
- Refs for DOM access only; `forwardRef`/ref props on design-system primitives.

## 6. Rendering performance

- Measure first (React DevTools Profiler, why-did-you-render, Lighthouse).
- Lift expensive work out of render or memoize it (`useMemo`) when profiling shows it matters; React Compiler (when enabled) handles most memoization.
- Split contexts so frequently-changing values don't re-render the whole tree; or use a store with selectors.
- Virtualize lists > ~200 rows (TanStack Virtual).
- Debounce input-driven queries (200–300ms); `useDeferredValue`/`startTransition` for heavy filtering.
- Lazy-load heavy client components (`next/dynamic`, `React.lazy`) — charts, editors, maps.
- Images: `next/image` / `<Image>` from the framework, explicit sizes, `priority` only for the LCP image.

## 7. TypeScript

- `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes` when feasible.
- Types flow from sources of truth: `z.infer`, generated OpenAPI types, Supabase `Database` types, Prisma/Drizzle inferred types.
- `unknown` + narrowing instead of `any`; `satisfies` for config objects; discriminated unions for states (`{ status: 'loading' } | { status: 'error', error } | { status: 'success', data }`).
- No `as` casts on external data — parse it.

## 8. Styling

- Tokens from `DESIGN.md` only; Tailwind with `cn()` (clsx + tailwind-merge) and `cva` for variants; or CSS Modules with variables.
- Logical properties for RTL (`ms-`, `pe-`, `start-`) — `i18n-rtl`.
- No inline style objects for static styles; no global CSS leaking from components.

## 9. Environment and config

- Validate env at startup (`launch-security` P1); client-exposed vars only with the framework prefix and only non-secret values.
- Feature flags read in one module; no `process.env` sprinkled through components.

## 10. React Native / Expo notes

- `FlatList`/`FlashList` for lists (never `ScrollView` + map for long lists), `keyExtractor` with IDs.
- `StyleSheet.create` or NativeWind with tokens; `marginStart`/`paddingEnd` for RTL.
- Navigation state via Expo Router; deep links for every screen.
- Avoid heavy JS on the main thread; Reanimated for animations; `InteractionManager` for post-transition work.
- Secure storage for tokens (`expo-secure-store`), not AsyncStorage (`launch-security` P1).

## 11. Vue / Nuxt and Svelte notes

- Vue: Composition API, `computed` for derived state (not watchers that set refs), Pinia for shared state, `useFetch`/`useAsyncData` in Nuxt for server data, `v-for` with `:key` from IDs.
- Svelte 5: runes (`$state`, `$derived`, `$effect` only for side effects), SvelteKit `load` for data, form actions with progressive enhancement.

## 12. Anti-patterns → fixes (fe_check.py)

| Anti-pattern | Fix |
|--------------|-----|
| `useEffect(() => setFull(first + last), [first, last])` | `const full = first + last` |
| `useEffect(() => { fetch(...).then(setData) }, [])` | server component / loader / `useQuery` |
| `key={index}` on dynamic lists | `key={item.id}` |
| `any`, `@ts-ignore` | parse with schema, `unknown`, fix the type; `@ts-expect-error` with reason if unavoidable |
| `console.log` in committed code | remove, or use the logger |
| `"use client"` at the top of `page.tsx`/`layout.tsx` | move interactivity into a small client child |
| `<img>` in Next.js | `next/image` with width/height |
| component defined inside component | move to module scope |
| 15 boolean props | variants + composition |
| `items.map(x => <Row/>)` without key | add a stable key |
