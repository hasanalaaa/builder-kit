# builder-kit — project facts

- Stack: a Claude Code plugin. Markdown skills plus stdlib-only Python 3.10+ scanners; no dependencies.
- Test: `make test` (every `test_*.py` prints `selftest OK`). Lint: `make lint` (ruff F/E9, `bash -n`, JSON). Gate: `make check` must say SHIP.
- Plugin checks: `claude plugin validate plugins/builder-kit` and `claude plugin validate .`. Behavior: `cd plugins/builder-kit && claude plugin eval .` (costs credits).
- Entry points: `plugins/builder-kit/skills/<skill>/SKILL.md`, `skills/ship/scripts/ship_check.py` (the gate), `hooks/post_edit.py` (edit hook), `action.yml` (GitHub Action), `lib/bk.py` (shared walk/waivers/report).
- Published contracts: skill names (`builder-kit:<skill>`), command names, `ship_check.py` flags and exit codes, the JSON finding shape `{level, rule, path, line, message}` (+ `scanner` in `--json`), `.builder-kit.json` format, `bk-ignore` comments, older per-tool ignore comments (`security-scan: ignore`, …), action inputs/outputs, `BUILDER_KIT_HOOKS` / `BUILDER_KIT_FORMAT`.
- Adding a scanner: tuples → `bk.report(findings, "<name>", root)`; register in `ship_check.scanners()` and the table in `skills/ship/references/lifecycle.md`; add `test_<name>.py` beside it. `tests/test_integrity.py` enforces all three.
- Known traps: scanner and test files contain the very patterns they detect (fake keys are split strings, e.g. `"sk_live_" + "…"`); keep them split and waived in `.builder-kit.json`, never real values. Skill descriptions must stay ≤ 1024 chars. The hook must never block on its own failure (it exits 0 on any exception).
- Release: bump `version` in `plugins/builder-kit/.claude-plugin/plugin.json`, add a CHANGELOG entry, then `claude plugin marketplace update builder-kit && claude plugin update builder-kit@builder-kit`.
- Never touch: users' `.env` files; never commit `SHIP_REPORT.md`, `*.sarif`, `evals/results/`.
