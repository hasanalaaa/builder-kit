---
name: ship
description: Load when asked what to check before launch or release, whether an app is ready, or how to build a whole product (شنو أفحص قبل الإطلاق، جاهز؟). The builder-kit conductor - runs a website, app or AI-built product through the whole lifecycle in the right order (idea → spec → stack → architecture → design → build slices → quality gates → release → operate) and decides which builder-kit skill applies at each moment. Ships ship_check.py, which runs every builder-kit scanner on a repo (security, architecture, errors, data, tests, front end, design, accessibility, RTL, AI, performance, SEO, release, observability, legal, mobile, docs) and gives one SHIP / BLOCKED verdict. Use when starting a project end to end, before merging or releasing, for a full quality check, when unsure which skill to use, or when the user says ship it, ready to launch?, full check, check everything, build the whole thing properly, جاهز للإطلاق, افحص كل شيء, ابنِ المشروع كامل.
---

# Ship (conductor)

builder-kit is a set of specialist skills. This one decides the order and holds the gates, so a project is built right from the first line and nothing is forgotten before launch.

| File | Use it for |
|------|-----------|
| `references/lifecycle.md` | The stage-by-stage map: which skill, which output, which gate, for new projects, features, launches and rescues; the skill router table |
| `scripts/ship_check.py` | Run all relevant builder-kit scanners in parallel and print one table and verdict. `--report FILE` Markdown, `--json FILE` every finding for agents, `--sarif FILE` GitHub code scanning; `--only` / `--skip` filter; `--with-tests` also runs the project's test command (npm/pnpm/yarn/bun `test`, pytest, or `make test`) |

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
Read each failing scanner's output (the report includes it), fix in severity order, re-run until SHIP. For a long list, `--json` gives every finding as `{scanner, level, rule, path, line, message}`: group by rule, fix the root cause once.

### Waivers (false positives and accepted risks)

Fix first. Waive only a finding you have read and can justify, always with the reason next to it:
- One line: a comment `bk-ignore: <rule> -- <reason>` on the line or the line above (bare `bk-ignore` waives every rule there; avoid it).
- One file: `bk-ignore-file: <rule> -- <reason>` anywhere in it (fixtures that hold the patterns on purpose).
- Folders or repo-wide findings: `.builder-kit.json` at the root, `{"ignore": {"<rule>": ["<glob>"]}, "why": {...}}`. Globs are fnmatch (`*` crosses folders); `"."` matches repo-wide findings like `no-changelog`; `"*"` as the rule waives everything under a glob (generated or vendored code only).
Never waive an ERROR from `security` or `data` without telling the user. The scanners' older per-tool comments (`security-scan: ignore`, `design-lint: ignore`, ...) still work. The edit hook honors the same waivers.

### In CI

The repo root is also a GitHub Action: one step runs the gate, writes the report to the job summary and SARIF for code-scanning annotations.
```yaml
permissions: { contents: read, security-events: write }
steps:
  - uses: actions/checkout@<sha>
  - id: gate
    uses: hasanalaaa/builder-kit@<sha>        # inputs: path, only, skip, sarif, fail-on-blocked
  - uses: github/codeql-action/upload-sarif@<sha>
    if: always()
    with: { sarif_file: "${{ steps.gate.outputs.sarif }}", category: builder-kit }
```

## 4. Done when (per mode)

- NEW: all stages' artifacts exist; LAUNCH checklist passed.
- FEATURE: per-slice gate passed; docs/maps updated.
- LAUNCH: `ship_check.py` SHIP with `--with-tests`; launch checklist in `lifecycle.md` §3 complete; `SECURITY_REPORT.md` current.
