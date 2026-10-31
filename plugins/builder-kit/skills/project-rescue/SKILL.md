---
name: project-rescue
description: Load when taking over an existing, messy or AI-built app (Lovable, Bolt, v0, Replit). Triage scan, stop the bleeding (keys, open DB, auth, payments), stabilize, safety-net tests, untangle in small steps. Triggers: fix my app, استلام مشروع, تطبيقي خربان.
---

# Project Rescue

A rescued project keeps working the whole time. Rescue is triage, not a rewrite: find what can hurt users or the owner right now (security, data loss, payments), fix that first, then build a safety net (deploy pipeline, error tracking, tests), and only then improve structure and UX in small steps. Rewrites of working products usually fail (global CLAUDE.md §5); a rescue earns trust step by step.

| File | Use it for |
|------|-----------|
| `references/playbook.md` | Phase-by-phase rescue (0 intake → 1 triage → 2 stop the bleeding → 3 stabilize → 4 safety net → 5 untangle → 6 improve), platform-specific issues (Lovable/Bolt/v0/Replit/Firebase/Supabase), rewrite-vs-rescue decision, owner communication, `RESCUE_REPORT.md` template |

## 1. Rules

1. **First, do no harm.** Read-only until you have: a backup of the database, the code in git with a clean starting commit, access to hosting/DB dashboards, and the owner's go-ahead.
2. **Severity order**: active security exposure and data loss → payments/money → broken core flow → deploy/ops → structure → UX polish.
3. **Every step lands working and is reversible**: small commits, deploy, verify, next.
4. **Safety net before refactor**: tests around the core flows (characterization tests that pin current behavior) before moving code.
5. **Rotate anything that was exposed** (keys in client code, git history, public repos) and assume it was used (`launch-security` 24–25, incident card).
6. **Keep the stack unless it blocks the product.** Lovable/Bolt/v0 output (React/Vite or Next + Supabase) is a fine base once structured.
7. **Report in plain language**: what was wrong, what's fixed, what remains, with evidence; the owner decides priorities for the rest.

## 2. Workflow

1. **Intake** (`playbook.md` §0): get access, backup, clean commit; fill `SECURITY_MAP.md` context block; ask the owner the 5 intake questions.
2. **Triage scan**: `python3 <builder-kit>/skills/ship/scripts/ship_check.py . --report` (runs every scanner: security, architecture, errors, design, a11y, RTL, data, tests, release, observability, legal, SEO/perf/mobile when relevant). Plus manual: the Top-10 rescue checks (`playbook.md` §1).
3. **Rescue plan**: a ranked list (Critical / High / Medium / Low) with effort, written to `RESCUE_REPORT.md`; review with the owner.
4. **Stop the bleeding** (Critical): exposed keys, open RLS/rules, auth bypass, payment trust issues, data loss risks. Fix, test, deploy, verify live.
5. **Stabilize**: reproducible build, env validation, CI, preview deploys, error tracking, uptime, backups (`deploy-release`, `observability`).
6. **Safety net**: E2E for the 3–5 core journeys + integration tests on critical endpoints (`testing-strategy`).
7. **Untangle**: `project-architecture` UNTANGLE playbook, in small steps, map first (`ARCHITECTURE.md`).
8. **Improve**: design system extraction and polish, performance, accessibility, i18n/RTL, SIMPLIFY.
9. **Hand off**: docs (`docs-handoff`), updated report, maintenance rhythm.

## 3. Done when (rescue phase complete)

- [ ] No Critical/High findings open; exposed secrets rotated; database access rules verified live.
- [ ] CI + preview deploys + error tracking + uptime + backups (restore tested).
- [ ] Core journeys covered by automated tests that pass in CI.
- [ ] `ARCHITECTURE.md` and project `CLAUDE.md` exist; `arch_check.py` 0 ERROR or a dated plan for the remaining items.
- [ ] `RESCUE_REPORT.md` delivered with before/after scanner counts and the remaining roadmap.
