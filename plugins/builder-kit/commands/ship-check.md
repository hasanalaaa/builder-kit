---
description: Run every builder-kit scanner on this repo and get one SHIP / BLOCKED verdict with a prioritized fix list
argument-hint: "[path] [--with-tests] [--only keys] [--report FILE] [--json FILE] [--sarif FILE]"
---

Run the builder-kit quality gate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/ship_check.py" $ARGUMENTS
```
(If no path was given, use `.`.)

Then:
1. Show the scanner table and the verdict.
2. For every scanner with ERRORs, read its full output (or rerun with `--json FILE` and read the findings) and list the findings grouped by severity, each with file:line, why it matters in one line, and the fix. Load the owning skill (`skills/ship/references/lifecycle.md` §5) for the fix standard.
3. Summarize WARNs by scanner in one line each; call out any that are risky. A finding you verified is a false positive: propose a waiver with its reason (`ship` skill, Waivers) instead of silently skipping it.
4. Ask me whether to fix the ERRORs now (in severity order, one commit per fix, re-running the scanner after each), unless I already said to fix them.

Do not change code before I answer, unless my arguments or message asked for fixes.
