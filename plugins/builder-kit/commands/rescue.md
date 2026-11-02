---
description: Take over a messy or AI-built project (Lovable, Bolt, v0, Replit, Cursor) and rescue it safely - triage, stop the bleeding, stabilize, test, untangle
argument-hint: "[path] [notes about what's broken]"
---

Rescue this project: $ARGUMENTS

Load the builder-kit `project-rescue` skill and follow it:

1. **Intake (read-only)**: confirm there is a clean git starting point and a database backup; if not, tell me exactly how to make them and wait. Fill the project context (stack, hosting, data, auth, users) from the code.
2. **Triage**: run `python3 "${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/ship_check.py" . --report RESCUE_SCAN.md` and the Top-10 manual rescue checks from `skills/project-rescue/references/playbook.md` §1.
3. **Rescue plan**: write `RESCUE_REPORT.md` with findings ranked Critical/High/Medium/Low, effort, and the owner actions only I can do (key rotation in dashboards, MFA). Explain risks in plain language.
4. **Stop and ask** before changing anything. After my OK, fix Critical items first, one small verified commit each, re-running the relevant scanner after every fix. Keep fixes single-threaded (no parallel slice-builders on an untested codebase); use `builder-kit:explorer` to locate code instead of reading the whole repo.

Never delete data, files I didn't create, or git history without asking.
