# Untangling a messy codebase

Goal: get from tangled to clean wiring **without stopping the app and without a rewrite**. Every step lands working and can ship on its own. Big-bang rewrites of working products fail far more often than they succeed. Don't propose one.

Rules for this whole playbook:
- Work on a branch; commit after every successful step so any step can be reverted.
- Never change behavior and structure in the same step. A move is a move; a fix is a fix.
- Ask before deleting files you didn't create or anything that looks like user data.
- Keep the user informed: show the as-is map and the target map before moving code.

---

## Step 1 · Measure the mess (read-only)

1. `python3 <skill>/scripts/arch_check.py .`: cycles, boundary leaks, god files, duplicates, junk drawers, versioned copies, commented-out code.
2. Dependency graph (JS/TS: dependency-cruiser; Python: `pydeps` or import-linter's reports).
3. **Hotspots:** files that change the most AND are the most complex are where tangle hurts.
   ```bash
   git log --since=12.months --format= --name-only | grep -v '^$' | sort | uniq -c | sort -rn | head -20
   ```
   Cross-check with file size or complexity. Big + frequently changed = top priority.
4. List parallel patterns: how many ways does the app fetch data, handle errors, manage state, read config, validate input, log?
5. Write the **as-is** section in `ARCHITECTURE.md`: honest, including the ugly parts.

## Step 2 · Draw the target map

Using SKILL.md §2: name the features, the shared kernel, the infra adapters, the single home for each concern, and the dependency rules. Agree it with the user. Record it as an ADR.

## Step 3 · Safety net

Before moving anything, add **characterization tests** for the critical flows (sign-up/login, the main user journey, payments, anything with money or data loss risk). They pin current behavior, bugs included, so moves can't silently change it. Prefer a few end-to-end or API-level tests over many brittle unit tests here.

## Step 4 · Move in this order

Each item is a series of small commits. Run tests + `arch_check` after each.

1. **Freeze the bleeding.** Add boundary rules in **warn** mode and the CLAUDE.md conventions block, so new code stops adding tangle while old code is fixed.
2. **Break import cycles.** For each cycle, either move the shared piece down into a lower module both can import, merge two modules that are really one, or invert the dependency (the lower module defines an interface/callback; the higher one supplies it). Never "fix" a cycle with lazy/dynamic imports.
3. **Consolidate duplicates into their single home.** Pick the best implementation, move it to its proper module, point every caller at it (one caller per commit if risky), delete the copies. Same for parallel patterns: choose one, migrate call sites, delete the others.
4. **Split god files.** Extract by responsibility (types → `schema`, queries → `data`, rules → `domain`, UI pieces → components). Keep the old file as a thin re-export only while migrating call sites, then delete it. Don't leave permanent shims.
5. **Move code into feature folders.** One feature at a time: create `features/<name>/index`, move its files in, update imports (use the editor/LSP rename/move refactor, not search-and-replace), run tests. Strangler-fig style: new code goes into the new structure from day one, old areas migrate as they're touched.
6. **Empty the junk drawers.** Every function in `utils/helpers/common` moves to the module that owns its meaning, or to a focused, well-named `shared/lib/<topic>` file. Delete the drawer when empty.
7. **Delete dead code** found by knip/vulture/staticcheck after checking for dynamic use. Delete commented-out code and `_v2/_old` files (Git keeps history).
8. **Flip boundary rules from warn to error** and tighten `arch_check` thresholds (ratchet).

## Step 5 · Finish

- `ARCHITECTURE.md` updated from "as-is" to the real current map.
- Report: what moved, what was deleted, before/after `arch_check` counts, what's still open and why.

---

## Breaking common tangles: quick recipes

| Tangle | Fix |
|---|---|
| Component fetches data, holds business rules and renders | Data access → `data/` or a hook; rules → `domain/` pure function; component only renders |
| Route handler with 200 lines of logic | Handler: validate + call service. Logic → `service`/`domain`. Queries → `data` |
| Same type defined in 5 files | One schema (e.g. Zod/Pydantic) in the owning module; infer types from it; import everywhere |
| Three API clients | One configured client in `shared/api` (or `infra/`), with auth, errors, retries in one place |
| Env vars read everywhere (`process.env.X` in 40 files) | One validated `config/env` module; everything imports from it |
| `utils.ts` with 60 unrelated functions | Move each to its owning module or to a named `shared/lib/<topic>` file |
| Feature A imports feature B's internals and vice versa | Extract the shared concept into its own module, or let one side publish events the other subscribes to |
| `try { … } catch {}` scattered | One error type hierarchy + one handler at the transport boundary; log with context; never swallow |
