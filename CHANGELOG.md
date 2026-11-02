# Changelog

## 2.3.0 — 2026-11-02

Built on what the evals showed: plain Claude already knows the rules, so the gains come from running things, stopping on failure, starting from tested code and remembering the repo.

### Added
- **Stop gate runs the project's own checks** (`hooks/project_checks.py`) on files changed this session: typecheck (`typecheck`/`type-check` script or local `tsc --noEmit`, `mypy`/`pyright` when configured), lint (`eslint`, `ruff`), related tests (`vitest related`, `jest --findRelatedTests`, matching `pytest` files, `go vet`/`go test` on changed packages). Only locally installed tools run, nothing is downloaded; errors in untouched files never block; missing tools and timeouts are skipped. `BUILDER_KIT_STOP_CHECKS=off` skips just this part. Stop hook timeout 30 → 120 s (checks budget 90 s).
- **`recipes` skill**: five tested code recipes for Next.js 16 + TypeScript + `pg` + zod 4: `file-upload` (magic bytes, size cap, random names), `stripe-webhook` (raw-body signature, `event.id` idempotency in the same transaction, migration), `owner-scoped-api` (session, strict zod, owner-scoped queries, capped pagination), `postgres-rls` (forced owner policies, `withUser()`, cross-user test), `ai-chat-stream` (auth, rate limit before spend, input caps, `max_tokens`, timeout, abort on disconnect). Each ships its own vitest suite (real Postgres via PGlite, real Stripe signatures); verified with `tsc`, `vitest` and `next build` in a fresh Next 16 app. `bk_add.py` copies one in without ever overwriting a file and prints deps, env vars, the test command and ADAPT notes.
- **Memory across sessions**: `repo_map.py` (project-architecture) prints a compact cached map of files and their key symbols within a token budget (~2.5k), so Claude reads one map instead of dozens of files. `lib/lessons.py` counts the rules each blocking stop caught, plus your own lessons (`lessons.py add "…"`). A new **SessionStart hook** shows up to 5 repeated lessons and the map command (~100 tokens). All stored in `.git/builder-kit/`, never in the working tree.
- **Browser check** (`frontend-quality/scripts/verify_ui.py`): opens the running app with the project's own Playwright at 375 and 1280 px and prints only what is broken: console and page errors, failed same-origin requests, sideways scroll on phones, images without alt or broken, axe-core violations, missing `dir="rtl"`. `--start "npm run dev"` runs the dev server and always kills its process group. Exit 3 when Playwright is missing (nothing is downloaded). Added to the LAUNCH checklist.
- **Model-routed agents**: `explorer` (haiku, read-only file:line locator) and `slice-builder` (sonnet, own git worktree, one slice with tests and evidence). `builder-reviewer` runs on opus with fresh-context discipline; `ui-reviewer` on sonnet. `/builder-kit:feature` and `/builder-kit:new-project` fan independent slices out in parallel, then review the combined diff; changes under 3 files stay single-threaded. `ai-workflow/references/orchestration.md` documents when to fan out.
- **Security rule `ssrf-follows-redirects`**: a file that checks for private addresses but lets `fetch` follow redirects is an ERROR (the redirect can land on an internal address). Found by the new link-preview eval, where both arms missed it.
- **Evals: 15 build tasks** (13 new: password reset, login, IDOR, invoice money, safe NOT NULL migration, pagination, outbound fetch, streaming chat, Arabic/English RTL, accessible form, receipt email, SSRF link preview, paid API key), 3 runs per arm. Every grader was checked offline against a hand-written correct solution and a careless one. `evals/README.md` covers running, cost (about $15–25 for the full two-arm suite) and comparing releases.

### Fixed
- Stop gate missed every change when Claude's cwd was a subfolder of the repo (porcelain paths are relative to the repo root).
- `schema_check` and `mobile_release_check` walked gitignored folders, so copies in `.claude/worktrees/` (now created by `slice-builder`) or build output produced wrong findings (e.g. `index-not-concurrent` on a table created in the same migration). Both use the shared gitignore-aware `bk.walk`.

### Changed
- Always-on cost ~3,582 → ~3,722 tokens (+2 agents, +1 skill description); the SessionStart hook adds ~60–100 tokens in git repos.

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
