# Changelog

## 2.1.0 — 2026-10-31

### Added
- **Waivers everywhere**: `bk-ignore: <rule> -- <reason>` (line), `bk-ignore-file: <rule>` (file) and `.builder-kit.json` `{"ignore": {"<rule>|*": [globs]}}` (folders, repo-wide findings). Honored by all 17 scanners, `ship_check` and the edit hook. A broken config fails the scan loudly; it never blocks an edit.
- **Machine-readable output**: `ship_check --json FILE` (every finding with scanner, rule, path, line) and `--sarif FILE` (SARIF 2.1.0 for GitHub code scanning). Scanners print JSON lines under `BUILDER_KIT_FORMAT=json`.
- **GitHub Action** (`action.yml` at the repo root): runs the gate, writes the report to the job summary, emits SARIF, exposes `verdict`.
- **Behavioral evals** (`plugins/builder-kit/evals/`, 9 cases for `claude plugin eval`): skill routing on natural Arabic and English prompts, answer quality graders, and a negative case. On-demand `evals` workflow.
- **Plugin integrity test**: skill names and description limits, cross-skill links, reference paths, a test beside every script, gate registry vs. `lifecycle.md`, manifest skill count.
- `make test`, `make lint` (ruff), `make check`; CI runs them plus the gate through the repo's own action, uploading SARIF on `main`.
- `ship_check --with-tests` runs `make test` when a Makefile has a `test:` target; `audit_tests` recognizes Makefile/justfile targets, Cargo, Gradle and Flutter.

### Changed
- All scanners report through one function (`lib/bk.py`), so text, JSON, waivers and summaries behave the same everywhere. Security findings show their check number in the message (`[07] ...`).
- `ship_check` drops a finding a previous scanner already reported (e.g. `no-env-example` from release and docs).
- One shared test-code pattern (`bk.TEST_CODE`) for every scanner; it now recognizes Kotlin/Java `src/test/`, `androidTest/`, `FooTest.kt`, `FooTests.swift`, `_test.dart`.
- Performance findings carry the file path, so they can be waived per file.

### Fixed
- `design-system` and `launch-security` skill descriptions were over the 1024-character limit (risk of truncation).
- `a11y_lint` no longer flags a dialog scrim/backdrop click handler as a non-interactive click.
- `security_scan` no longer flags `http://host` URL templates in docs and comments.
- Docs: Next.js 16 renamed `middleware.ts` to `proxy.ts`.
- Unused imports in `security_scan.py` and `arch_check.py`.

## 2.0.0 — 2026-10-30

First public release: 26 skills, 17 scanners, the `ship` gate, the edit-time hook, 4 commands, 2 reviewer agents, CI.
