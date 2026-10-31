---
description: Build one feature as a verified vertical slice - mini spec, placement, security, data/API/UI, tests, per-slice gate
argument-hint: "<feature description>"
---

Build this feature: $ARGUMENTS

Follow the builder-kit `ship` skill FEATURE flow (`skills/ship/references/lifecycle.md` §2) with the `ai-workflow` loop:

1. Read `SPEC.md`, `ARCHITECTURE.md`, `DESIGN.md` and the code the feature touches. Write a mini spec (goal, acceptance criteria incl. unhappy paths, files likely touched, out of scope) and a short plan. Wait for my OK on the plan.
2. Place the code per `project-architecture` BUILD (search before creating; follow the nearest sibling).
3. Apply the specialist skills the feature needs (security rules, data-design, api-contracts, design-system + frontend-quality for UI, error-handling, i18n-rtl, payments-billing, ai-features, email-notifications…).
4. Write tests from the acceptance criteria; run them.
5. Per-slice gate: project tests green and `python3 "${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/ship_check.py" . --only security,architecture,errors,frontend,design,a11y,rtl,data` with 0 ERROR. For UI, look at it at 375 and 1280 px, Arabic and English, light and dark.
6. Show me the outputs and the diff summary; update the docs/maps that changed.
