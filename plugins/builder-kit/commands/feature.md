---
description: Build one feature as a verified vertical slice - mini spec, placement, security, data/API/UI, tests, per-slice gate
argument-hint: "<feature description>"
---

Build this feature: $ARGUMENTS

Follow the builder-kit `ship` skill FEATURE flow (`skills/ship/references/lifecycle.md` §2) with the `ai-workflow` loop and its orchestration pattern (`skills/ai-workflow/references/orchestration.md`):

1. **Map, then plan (main thread).** If you don't know where the feature lives, ask `builder-kit:explorer` instead of reading the repo yourself. Read `SPEC.md`, `ARCHITECTURE.md`, `DESIGN.md` and the code the plan hinges on. Write a mini spec (goal, acceptance criteria incl. unhappy paths, files likely touched, out of scope) and a plan split into slices, each with its own files and criteria. Wait for my OK on the plan.
2. **Choose the mode.** Under 3 files, or only one slice, or slices that share files: build it yourself here, single-threaded (fan-out costs more than it saves). Otherwise commit the plan, note the base SHA, and spawn one `builder-kit:slice-builder` per independent slice **in parallel**, each with the base SHA, its goal, criteria, allowed files and out-of-scope list. Slices that depend on another slice wait for it.
3. **Build** (single-threaded): place the code per `project-architecture` BUILD (search before creating; follow the nearest sibling), apply the specialist skills the feature needs (security rules, data-design, api-contracts, design-system + frontend-quality for UI, error-handling, i18n-rtl, payments-billing, ai-features, email-notifications…), write tests from the acceptance criteria and run them.
4. **Merge** (fan-out): for each DONE slice, merge its branch; for BLOCKED, decide here (fix the plan, or build it yourself). Re-run the project tests on the merged result.
5. **Review** (after fan-out, or any change touching auth, money, permissions, data deletion or migrations). Spawn `builder-kit:builder-reviewer` on `<base-sha>..HEAD` with the mini spec only, never your summary of the work. For UI, also `builder-kit:ui-reviewer`. Fix Critical/High findings.
6. **Gate**: project tests green and `python3 "${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/ship_check.py" . --only security,architecture,errors,frontend,design,a11y,rtl,data` with 0 ERROR. For UI, look at it at 375 and 1280 px, Arabic and English, light and dark.
7. Show me the outputs and the diff summary; update the docs/maps that changed.
