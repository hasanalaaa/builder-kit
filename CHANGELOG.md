# Changelog

## 2.2.0 — 2026-10-31

### Added
- **Stop gate** (`hooks/stop_gate.py`): Claude can't end its turn while files it changed this session still have blocking findings. Uses the edit hook's scanners and waivers, ignores changes made before the session, blocks at most once per stop, costs no tokens when the code is clean. Works even when no skill fired.
- **Build-task evals** (`build-avatar-upload`, `build-stripe-webhook`): a scaffolded repo, Claude writes the real file, graders read the file. First run: with the plugin 1.00 / 1.00, without 0.80 / 0.86 (missed magic-byte checks on uploads and `event.id` dedupe on webhooks: XSS and double credits).

### Changed
- **Always-on cost 8,891 → 3,582 tokens per session (−60%)**: every skill and agent description rewritten to ~250 chars, trigger first, Arabic and English trigger words kept.
- On-invoke cost: launch-security 7.9k → 6.3k (AUDIT workflow moved to `references/audit-workflow.md`), project-architecture 6.7k → 5.8k (NEW/UNTANGLE/SIMPLIFY moved to `references/workflows.md`). The rules used on every edit stay in SKILL.md.
- `post_edit.py` exposes `blocking_errors()` and `describe()` shared with the Stop gate.

## 2.1.1 — 2026-10-31

Tuned from the first real eval run (`claude plugin eval`, 9 cases, with vs. without the plugin).

### Fixed
- 4 of 8 skills didn't fire on natural prompts (accessibility, ai-features, launch-security, ship). Their descriptions now open with a direct trigger ("Load before writing a route handler, upload, webhook…", "شنو أفحص قبل الإطلاق"); all 8 fire.
- `ai-features` workflow states what every chat/stream endpoint shows in code (max tokens, timeout, quota check, abort reaching the provider); `payments-billing` spells out the webhook handler (raw-body signature, `event.id` unique in the same transaction, fast 200, queue).

### Changed
- Eval graders now check what builder-kit adds over a plain answer (return focus, magic bytes + random names + signed URLs, `<bdi>` isolation, FK indexes + RLS, transaction + fast ack, contrast ratios) instead of things any answer contains. Mean Δ went from +0.04 to +0.11.
- `ai-chat-streaming` prompt asks for the code (the empty eval workspace made the agent ask where the app is).

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
