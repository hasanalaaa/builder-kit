# Project architecture: NEW, UNTANGLE and SIMPLIFY workflows

### 3.1 NEW: starting a project

1. **Clarify** the product's core capabilities (these become the features), the stack, and where it runs. Ask only for what you can't decide sensibly; state assumptions.
2. **Pick the layout** for the stack from `references/layouts.md`.
3. **Write the map first:** `ARCHITECTURE.md` from the template, a conventions block in `CLAUDE.md` (and `AGENTS.md` if other agents are used), and `docs/adr/0001-stack-and-architecture.md`.
4. **Build a walking skeleton:** one real feature wired end to end through every layer (UI → transport → use case → domain → data → database), with its tests. This proves the wiring before anything is copied.
5. **Install the guard rails on day one** (`references/enforcement.md`): formatter, linter, strict types, boundary rules, test runner, pre-commit hook, CI running all of them plus `arch_check.py`.
6. Run `python3 scripts/arch_check.py <repo>` and fix every ERROR before adding the next feature.

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
