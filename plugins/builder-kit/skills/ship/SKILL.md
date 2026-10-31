---
name: ship
description: The builder-kit conductor - runs a website, app or AI-built product through the whole lifecycle in the right order (idea → spec → stack → architecture → design → build slices → quality gates → release → operate) and decides which builder-kit skill applies at each moment. Ships ship_check.py, which runs every builder-kit scanner on a repo (security, architecture, errors, data, tests, front end, design, accessibility, RTL, AI, performance, SEO, release, observability, legal, mobile, docs) and gives one SHIP / BLOCKED verdict. Use when starting a project end to end, before merging or releasing, for a full quality check, when unsure which skill to use, or when the user says ship it, ready to launch?, full check, check everything, build the whole thing properly, جاهز للإطلاق, افحص كل شيء, ابنِ المشروع كامل.
---

# Ship (conductor)

builder-kit is a set of specialist skills. This one decides the order and holds the gates, so a project is built right from the first line and nothing is forgotten before launch.

| File | Use it for |
|------|-----------|
| `references/lifecycle.md` | The stage-by-stage map: which skill, which output, which gate, for new projects, features, launches and rescues; the skill router table |
| `scripts/ship_check.py` | Run all relevant builder-kit scanners in parallel and print one table and verdict. `--report FILE` writes a Markdown report; `--only` / `--skip` filter; `--with-tests` also runs the project's test command |

## 1. Rules

1. **Order matters**: spec before stack, stack before architecture, architecture and design before features, gates before release (`lifecycle.md`).
2. **Every stage leaves an artifact** in the repo: `SPEC.md`, ADR, `ARCHITECTURE.md`, `DESIGN.md`, tests, CI, reports. The next stage reads it.
3. **Gates are binary**: `ship_check.py` 0 ERROR plus the project's own tests green, or it doesn't ship. WARNs are fixed or written down with a reason.
4. **Load the specialist skill for the work at hand** (router in `lifecycle.md` §6); don't improvise standards a skill already defines.
5. **Small slices, always working** (`ai-workflow`): each slice passes the per-slice gate before the next starts.

## 2. Modes

- **NEW**: idea → launched product. Follow `lifecycle.md` §1 stages 0–8.
- **FEATURE**: one change in an existing product. `lifecycle.md` §2.
- **LAUNCH**: pre-release gate. `lifecycle.md` §3.
- **RESCUE**: inherited/messy project. `project-rescue` (uses `ship_check.py --report` for triage).
- **CHECK**: just run the gate: `python3 <skill>/scripts/ship_check.py <repo>`.

## 3. Running the gate

```bash
python3 <builder-kit>/skills/ship/scripts/ship_check.py .                      # all relevant scanners
python3 <builder-kit>/skills/ship/scripts/ship_check.py . --report SHIP_REPORT.md
python3 <builder-kit>/skills/ship/scripts/ship_check.py . --only security,architecture,errors
python3 <builder-kit>/skills/ship/scripts/ship_check.py . --with-tests           # also runs the project's test script
```
Read each failing scanner's output (the report includes it), fix in severity order, re-run until SHIP.

## 4. Done when (per mode)

- NEW: all stages' artifacts exist; LAUNCH checklist passed.
- FEATURE: per-slice gate passed; docs/maps updated.
- LAUNCH: `ship_check.py` SHIP with `--with-tests`; launch checklist in `lifecycle.md` §3 complete; `SECURITY_REPORT.md` current.
