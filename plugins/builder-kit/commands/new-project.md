---
description: Start a new app/site the builder-kit way - spec, stack, architecture, security baseline, design system, pipeline, then slices
argument-hint: "<idea in a sentence> [platforms] [languages]"
---

Start a new project for: $ARGUMENTS

Follow the builder-kit `ship` skill, NEW mode (`skills/ship/references/lifecycle.md` §1), stage by stage. Load each stage's skill before doing its work and stop at each gate:

1. **product-spec**: ask only the questions that change what gets built (max 7, with defaults), then write `SPEC.md` (scope Must/Later/Never, stories with acceptance criteria, non-functional targets incl. Arabic/RTL and ASVS level, slices). Show scope + assumptions + slices and wait for my OK.
2. **stack-picker**: choose the stack from the spec; write `docs/adr/0001-stack.md`; confirm versions from official sources.
3. **project-architecture** NEW: `ARCHITECTURE.md`, folder skeleton, boundary rules, guard rails.
4. **launch-security** BUILD baseline: env validation, auth helpers, error boundary, headers, RLS/owner scoping, `SECURITY_MAP.md`.
5. **design-system** DIRECTION: run `design_search.py --recommend`, propose 2–3 directions, generate tokens with `palette.py`, write `DESIGN.md`; plus `i18n-rtl` setup.
6. **deploy-release** + **observability** + **testing-strategy**: CI, preview deploys, error tracking, health endpoint, first integration test; project `CLAUDE.md` (draft with `ai-workflow/scripts/context_pack.py`).
7. Walking skeleton deployed; then build slice 1 with the `ai-workflow` loop.

After each stage, run `python3 "${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/ship_check.py" . --only <relevant keys>` and show me the result. Never skip a gate; tell me when a decision is mine.
