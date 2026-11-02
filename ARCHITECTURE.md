# Architecture

```
.claude-plugin/marketplace.json      marketplace entry (source: ./plugins/builder-kit)
action.yml                           GitHub Action → ship_check.py (report, JSON, SARIF, verdict output)
Makefile, ruff.toml                  test / lint / check
.builder-kit.json                    this repo's own waivers (with reasons)
plugins/builder-kit/
  .claude-plugin/plugin.json         manifest (version)
  skills/<skill>/                    one specialist standard each
    SKILL.md                         when to use, rules, workflow (loaded on demand)
    references/*.md                  long material, loaded only when the SKILL.md points to it
    scripts/<tool>.py + test_*.py    stdlib scanners/tools, each with a self-test
    data/*.csv                       design-system database
  skills/ship/scripts/ship_check.py  the gate: picks relevant scanners, runs them in parallel, dedupes, verdict
  lib/bk.py                          shared by every scanner: walk(), waivers, report() text/JSON
  hooks/post_edit.py                 PostToolUse hook: per-file scan of the edited file, blocks on ERROR only
  hooks/stop_gate.py + project_checks.py  Stop hook: scanners + the project's typecheck/lint/related tests on files changed this session
  hooks/session_start.py             SessionStart hook: repeated lessons + the repo-map command (~100 tokens)
  lib/lessons.py                     per-repo lessons memory in <git-common-dir>/builder-kit/lessons.json
  commands/*.md, agents/*.md         slash commands; subagents routed by model (explorer haiku, slice-builder sonnet, reviewers)
  tests/test_integrity.py            cross-file consistency
  evals/<case>/                      claude plugin eval suite
```

## Rules

- Dependencies point one way: `ship_check` → scanner scripts (subprocess) → `lib/bk.py`. The hook imports scanner modules directly and `lib/bk.py`. Scanners never import each other (except `palette.py` → `contrast.py` inside design-system).
- Scanners are stdlib only and read-only: they never modify the scanned repo.
- One finding shape after `bk.normalize`: `(level, rule, path, line, message)`, path relative to the scanned root, `.` for repo-wide.
- The gate talks to scanners only through their CLI (`BUILDER_KIT_FORMAT=json` lines plus the `N ERROR, M WARN` summary), so a crashing scanner is reported, never fatal.
- Skills hold standards; scripts hold checks. A rule enforced by a script is also written in its skill.
