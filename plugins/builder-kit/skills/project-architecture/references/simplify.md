# Simplify: same capability, less code, fewer steps

The best version of a feature does exactly what the longer one did, with fewer lines to read, fewer concepts to hold, and fewer steps for the user. Shorter code is easier for a human or an AI to understand, review, fix and change. But **clear beats short**: the goal is fewer *concepts*, not fewer characters. No code golf, no clever one-liners, no nested ternaries.

---

## 1. The shortening ladder (stop at the first rung that works)

1. **Delete it.** Is this code, option, screen or step needed at all? Unused features, flags, parameters, branches and fallbacks go.
2. **Reuse what exists** in this codebase (law 6).
3. **Use the platform:** the language's standard library, the browser (HTML/CSS), the database (constraints, defaults, generated columns, RLS).
4. **Use the framework's built-in feature** instead of hand-rolled machinery (forms, routing, caching, data fetching, validation).
5. **Use an already-installed library** that does it.
6. **Describe it as data** (a table/config/map) instead of repeating code.
7. **Generalize on the third copy:** two similar blocks may stay; the third becomes one function/component with parameters.
8. Only then write new code, as the simplest straight-line version.

---

## 2. Code patterns: before → after

Each pair has identical behavior. Apply only when that's true (see §5).

**Guard clauses instead of nesting**
```ts
// before
function price(user, cart) {
  if (user) {
    if (cart.items.length > 0) {
      return total(cart) - discount(user);
    } else { return 0; }
  } else { throw new HttpError(401, 'Unauthorized'); }
}
// after
function price(user, cart) {
  if (!user) throw new HttpError(401, 'Unauthorized');
  if (cart.items.length === 0) return 0;
  return total(cart) - discount(user);
}
```

**A lookup table instead of an if/switch chain**
```ts
// before: 14 lines of switch(status) { case 'paid': return 'green'; ... }
// after
const STATUS_COLOR = { paid: 'green', pending: 'amber', failed: 'red', refunded: 'gray' } as const;
const color = STATUS_COLOR[status];
```

**Derive state, don't sync it (React)**
```tsx
// before
const [items, setItems] = useState<Item[]>([]);
const [total, setTotal] = useState(0);
useEffect(() => { setTotal(items.reduce((s, i) => s + i.price, 0)); }, [items]);
// after
const [items, setItems] = useState<Item[]>([]);
const total = items.reduce((s, i) => s + i.price, 0);
```

**One schema, inferred types (no duplicated shapes)**
```ts
// before: interface Order {...} + a separate Zod schema + a separate form type, all drifting
// after
export const Order = z.object({ id: z.string().uuid(), quantity: z.number().int().min(1) });
export type Order = z.infer<typeof Order>;
```

**Remove pass-through wrappers**
```ts
// before
export function getUserById(id: string) { return userRepo.getUserById(id); }
// after: callers import userRepo.getUserById directly (or the feature's index re-exports it)
```

**Native HTML/CSS instead of JavaScript**
```html
<!-- before: a custom dropdown component with open/close state, click-outside listener and keyboard handling -->
<!-- after -->
<details><summary>Filters</summary> … </details>
<input type="date" required min="2026-01-01">
<dialog id="confirm">…</dialog>
```
Also: CSS `:hover`/`:focus-visible` instead of hover state in JS, CSS grid/flex instead of layout math, `loading="lazy"` instead of a lazy-load script, form `required`/`pattern` for instant feedback (the server still validates).

**Framework features instead of hand-rolled plumbing**
- A data-fetching library or server components instead of `useEffect` + `useState` for `data`, `loading`, `error`.
- Server actions / form actions instead of a custom fetch + loading-state + error-state per form.
- The router's loading/error boundaries instead of per-page spinners and try/catch.
- Database constraints (`unique`, `check`, `not null`, foreign keys) instead of application checks that race.

**Data-driven repetition**
```tsx
// before: five near-identical <Card> blocks
// after
const FEATURES = [
  { icon: Lock, title: 'Secure', body: '…' },
  { icon: Zap, title: 'Fast', body: '…' },
];
{FEATURES.map((f) => <FeatureCard key={f.title} {...f} />)}
```

**One error boundary instead of try/catch everywhere**: let errors propagate to the transport layer's single handler (launch-security secure-patterns P3). Catch only where you can actually recover.

**Optional chaining and defaults** instead of manual null ladders: `user?.profile?.name ?? 'Guest'`.

**Delete:** unused exports, unused parameters, impossible branches, options nobody sets, commented-out code, logging left from debugging, compatibility code for callers that no longer exist.

### What NOT to do in the name of "short"
- Nested ternaries, chained one-liners that need a debugger to understand, cryptic names (`d`, `tmp2`, `x`).
- Merging two functions that look alike but change for different reasons (they'll need to split again).
- Removing an explanatory variable that names a non-obvious value.
- Removing validation, authorization, error handling, accessibility or security checks. They are features, not length.
- A "generic" abstraction with more parameters than the copies it replaced.

---

## 3. UX patterns: fewer clicks, fewer steps, same result

Measure **steps-to-goal** for each key task (sign up, main action, checkout, settings change): count screens, clicks, fields and waits. Then shorten:

| Instead of | Do |
|---|---|
| Long sign-up forms | Email + password (or a passkey / social / magic link); ask for the rest later, when it's needed |
| Optional fields up front | Remove them, or move them behind "More options" (progressive disclosure) |
| Separate edit pages | Inline editing in place |
| A Save button + "unsaved changes" warnings | Autosave with a visible "Saved" state (where data loss is impossible) |
| "Are you sure?" dialogs for reversible actions | Do it immediately and offer Undo |
| Multi-step wizards for simple tasks | One screen; split only when steps are truly sequential |
| Empty forms | Smart defaults: last used values, detected locale/currency/time zone, prefill from context |
| Navigating menus to find things | Search, recent items, direct links, keyboard shortcuts for power users |
| Repeating an action per item | Bulk select + one action |
| Several competing buttons | One clear primary action per screen |
| Error messages after submit | Inline, field-level, as-you-type validation (server validation still runs) |

Never "simplify" away: re-authentication for sensitive account changes, payment confirmation, confirmation for destructive irreversible actions, store-required elements (launch-security S2/S3), consent, accessibility (labels, focus order, contrast, keyboard use).

---

## 4. SIMPLIFY workflow

1. **Baseline.** Tests green. Record `python3 scripts/arch_check.py . --stats` (lines, files, functions over budget, duplicates) and steps-to-goal for the key flows.
2. **Lock behavior.** If the area lacks tests, add characterization tests first (inputs → outputs, error cases, side effects).
3. **List candidates**, ranked by (lines or steps removed × clarity gained) ÷ risk: dead code, duplicates, pass-through layers, verbose patterns from §2, unused options, extra UX steps from §3.
4. **One simplification per commit.** Apply it, run tests + lint + types + `arch_check`.
5. **Prove equivalence** with the §5 checklist. If any item can't be shown, revert that change.
6. **Report** a before/after table: lines, files, functions over budget, duplicate blocks, steps-to-goal, plus the evidence (test names) that behavior is unchanged.

---

## 5. Equivalence checklist (all must hold)

- [ ] Same outputs for the same inputs, including empty, null, zero, one, very large and invalid inputs.
- [ ] Same errors and status codes on failure paths.
- [ ] Same side effects (writes, emails, events, logs) in the same order, and the same transaction boundaries.
- [ ] Same authorization and validation (nothing skipped).
- [ ] Same or better performance class (no N+1 queries introduced, no extra renders in hot paths).
- [ ] Same accessibility (labels, roles, keyboard, focus) and same visible behavior unless the user approved a UX change.
- [ ] Public APIs, URLs, database schema and persisted formats unchanged, or changed only with the user's approval and a migration.
- [ ] Tests that passed before still pass, unweakened.
