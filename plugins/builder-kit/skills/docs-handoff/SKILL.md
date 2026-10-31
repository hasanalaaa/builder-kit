---
name: docs-handoff
description: Load when finishing a milestone, handing over to a client or developer, or when docs are missing or stale. README, CLAUDE.md facts, ARCHITECTURE.md, runbooks, CHANGELOG, handover package. Triggers: README, documentation, handover, توثيق, تسليم المشروع.
---

# Docs and Handoff

Good docs are the cheapest form of reliability: they turn "only the original builder (or that one AI session) knows" into "anyone can run it". Write the minimum that answers real questions, keep it next to the code, and verify it by following it from a clean machine.

| File | Use it for |
|------|-----------|
| `references/templates.md` | README, project CLAUDE.md, runbooks (deploy, rollback, incident, key rotation, restore), onboarding, CHANGELOG, API docs, user help docs, client handover package and checklist |
| `scripts/docs_check.py` | Check that README, CLAUDE.md/AGENTS.md, ARCHITECTURE.md, .env.example, CHANGELOG and runbooks exist; README has setup/run/test/deploy sections; every `npm run`/`pnpm`/`make` command mentioned in docs exists; env vars documented match code |

## 1. Rules

1. **Docs live in the repo**, versioned with the code, in Markdown. Links to external tools for things that live there (dashboards, tickets).
2. **README gets a new person running locally in ≤ 15 minutes**: prerequisites, setup, env, run, test, common problems.
3. **Project `CLAUDE.md`/`AGENTS.md`** holds the facts AI agents need (global CLAUDE.md §10); draft with `ai-workflow/scripts/context_pack.py`.
4. **Explain why, not what**: decisions in ADRs, structure in `ARCHITECTURE.md`, design in `DESIGN.md`, product in `SPEC.md`. Code explains the what.
5. **Runbooks for anything done under stress**: deploy, rollback, incident response, restoring a backup, rotating keys, handling a payment dispute.
6. **Docs are tested**: follow the README on a clean clone; `docs_check.py` catches commands that don't exist and undocumented env vars.
7. **Update docs in the same change** that makes them wrong.
8. **Handover transfers ownership, not just files**: accounts, billing, domains, store accounts, credentials (rotated), and a maintenance plan.
9. **Bilingual where the audience is**: user-facing help in Arabic and English; developer docs in the team's working language.

## 2. Workflow: project or milestone handoff

1. Run `python3 <skill>/scripts/docs_check.py .`; fill gaps from `templates.md`.
2. Follow README from a clean clone (or ask a fresh AI session to do it) and fix every snag.
3. Write runbooks; link dashboards.
4. Client handover package (`templates.md` §8): accounts/ownership transfer, credentials rotated and delivered through a password manager, costs, maintenance rhythm (`launch-security` review-and-report maintenance table), known issues and roadmap.
5. Walkthrough session (recorded): architecture, deploy, where things live, how to get help.

## 3. Done when

- [ ] `docs_check.py` 0 ERROR.
- [ ] Clean-clone setup works by following the README alone.
- [ ] CLAUDE.md/AGENTS.md, ARCHITECTURE.md, SPEC.md, DESIGN.md current; ADRs for major decisions.
- [ ] Runbooks for deploy, rollback, incident, restore, key rotation.
- [ ] Handover: ownership of accounts transferred, credentials rotated and delivered securely, costs and maintenance plan documented.
