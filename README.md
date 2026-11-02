# builder-kit

[![ci](https://github.com/hasanalaaa/builder-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/hasanalaaa/builder-kit/actions/workflows/ci.yml) [![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Claude Code plugin that builds websites, web apps, mobile apps and AI-built ("vibe-coded") products the way senior teams do: from idea to launch and operation. It ships 27 skills, 5 tested code recipes, 25+ tested tools, one quality gate (also a GitHub Action with SARIF), hooks that keep Claude from finishing while its changes fail the scanners or the project's own typecheck and tests, per-repo memory, a real-browser check, model-routed agents and a 15-task build eval suite.

## Skills

| Stage | Skill | What it does | Tools |
|-------|-------|-------------|-------|
| Plan | `product-spec` | Idea → `SPEC.md`: scope Must/Later/Never, stories with testable acceptance criteria, non-functional targets, vertical slices | |
| Plan | `stack-picker` | Boring, AI-friendly stack and providers per project type, ADR with costs and exit plans | |
| Structure | `project-architecture` | Clean mapped structure, eleven laws, BUILD/UNTANGLE/SIMPLIFY | `arch_check.py`, `repo_map.py` (compact cached file/symbol map) |
| Security | `launch-security` | 27 checks + bonus/advanced/platform/store checks, first-attempt protocol, secure patterns, audit + report | `security_scan.py`, `find-secrets.sh`, `check-exposed.sh`, `check-headers.sh` |
| Data | `data-design` | Schemas, constraints, indexes, money/time types, multi-tenancy, zero-downtime migrations, query performance | `schema_check.py` |
| API | `api-contracts` | Naming, status codes, RFC 9457 errors, pagination, idempotency, versioning, OpenAPI, webhooks | |
| Reliability | `error-handling` | Error model, boundaries, timeouts, retries/backoff, circuit breakers, offline | `error_scan.py` |
| Quality | `testing-strategy` | Acceptance criteria → tests, levels per stack, E2E rules, flakiness, CI gates | `audit_tests.py` |
| UI code | `frontend-quality` | State placement, data fetching, RSC boundary, forms, components, TS strictness | `fe_check.py`, `verify_ui.py` (real browser: console, requests, mobile overflow, axe, RTL) |
| Design | `design-system` | Visual direction, tokens, color/type/layout/motion/copy, 30 components, screen patterns, critique and polish; a design database (40 product types, 22 styles, 36 palettes, 30 Arabic+Latin font pairings, 110 UX rules, landing and chart guides) | `design_search.py`, `palette.py`, `contrast.py`, `design_lint.py` |
| Arabic | `i18n-rtl` | RTL done right, logical properties, mirroring, bidi, ICU plurals, Intl formatting, Hijri, Arabic search, hreflang | `rtl_lint.py` |
| Inclusion | `accessibility` | WCAG 2.2 AA, keyboard, screen readers, ARIA patterns, native a11y, legal notes | `a11y_lint.py` |
| AI | `ai-features` | Server-side LLM calls, streaming, structured output, tools/agents, RAG, evals, cost/latency control, safety | `ai_check.py` |
| Money | `payments-billing` | Checkout, subscriptions, entitlements, webhooks, dunning, tax, refunds, Gulf methods, in-app purchases | |
| Messaging | `email-notifications` | Email DNS/deliverability, templates incl. RTL, queues, push, SMS/WhatsApp OTP, preferences | `check-email-dns.sh` |
| Speed | `performance` | Core Web Vitals, images, fonts, JS weight, caching, backend, mobile, budgets in CI | `perf_budget.py` |
| Growth | `seo-discoverability` | Technical SEO, metadata, JSON-LD, social cards, multilingual/Arabic SEO, AI search | `seo_check.py` |
| Ship | `deploy-release` | Environments, CI/CD, previews, secrets, migrations in deploy, rollouts, rollback, launch day | `release_check.py` |
| Operate | `observability` | Structured logs, Sentry, metrics, tracing, uptime, alerts/SLOs, analytics, RUM | `obs_check.py` |
| Compliance | `legal-compliance` | Data inventory, privacy/terms, consent, user rights, retention, GDPR/PDPL/CCPA, store privacy | `legal_check.py` |
| Mobile | `mobile-release` | Identity, signing, EAS, TestFlight/Play tracks, permissions, privacy manifest, rejections, OTA, rollouts | `mobile_release_check.py` |
| Workflow | `ai-workflow` | Working with AI agents: context files, plan→execute→verify, checkpoints, loop-breaking, prompts | `context_pack.py` |
| Build | `recipes` | Tested copy-in code for uploads, Stripe webhooks, owner-scoped CRUD, Postgres RLS and streaming AI chat (Next.js/TS), each with its own vitest suite | `bk_add.py` (never overwrites) |
| Rescue | `project-rescue` | Take over Lovable/Bolt/v0/Replit apps: triage, stop the bleeding, stabilize, safety net, untangle | uses `ship_check.py` |
| Fixing | `debugging` | Reproduce → minimize → hypothesize → bisect → root-cause fix → regression test; bug-class catalog | |
| Handoff | `docs-handoff` | README, CLAUDE.md, runbooks, onboarding, changelog, client handover package | `docs_check.py` |
| Conductor | `ship` | Lifecycle map, skill router, and the gate | `ship_check.py` (runs all scanners → SHIP/BLOCKED) |

## Commands, hook, agents

- `/builder-kit:new-project <idea>`: spec → stack → architecture → security → design → pipeline → slices, with gates.
- `/builder-kit:feature <feature>`: one verified vertical slice.
- `/builder-kit:ship-check [path]`: every scanner, one verdict, prioritized fixes.
- `/builder-kit:rescue [path]`: safe takeover of a messy or AI-built project.
- **Hooks** (cost no tokens unless they find something):
  - `PostToolUse` on Write/Edit: scans each edited file with the security, error, design, accessibility and RTL scanners and sends blocking findings back to Claude.
  - `Stop`: Claude can't end its turn while files it changed this session still have blocking findings, or fail the project's own typecheck, lint or related tests (only locally installed tools; errors in untouched files never block; blocks once, never loops; changes made before the session are ignored). Skip just the project checks with `BUILDER_KIT_STOP_CHECKS=off`.
  - `SessionStart`: up to 5 lessons for this repo (rules the Stop gate kept catching, plus your own) and the repo-map command, ~100 tokens. Silent outside git.
  - Turn all of them off with `BUILDER_KIT_HOOKS=off`.
- **Memory across sessions**: every blocking stop counts its rules in `.git/builder-kit/lessons.json`; add your own with `python3 plugins/builder-kit/lib/lessons.py add "Money is integer cents"` (`list`, `clear`). `repo_map.py` prints a ~2.5k-token map of files and their key symbols, cached until files change, so Claude reads one map instead of dozens of files. Nothing lands in your working tree.
- **Agents** (each on the model that fits the job):
  - `explorer` (haiku): where is X / what calls Y; returns a file:line table, never file dumps.
  - `slice-builder` (sonnet, own git worktree): implements one planned slice with tests and evidence; `/builder-kit:feature` runs independent slices in parallel (changes under 3 files stay single-threaded).
  - `builder-reviewer` (opus): fresh-context review of the combined diff against every standard.
  - `ui-reviewer` (sonnet): scores rendered UI with the design rubric, using `verify_ui.py` when available.

## Use the gate in any repo's CI

The repo root is a GitHub Action. It runs every relevant scanner, writes the report to the job summary, and emits SARIF so findings show up as code-scanning annotations on the diff.

```yaml
permissions: { contents: read, security-events: write }
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - id: gate
        uses: hasanalaaa/builder-kit@main   # pin a commit SHA in production
        with:
          skip: seo                          # optional: path, only, skip, sarif, fail-on-blocked
      - uses: github/codeql-action/upload-sarif@v4
        if: always()
        with: { sarif_file: "${{ steps.gate.outputs.sarif }}", category: builder-kit }
```
Locally: `python3 plugins/builder-kit/skills/ship/scripts/ship_check.py <repo> [--report F.md] [--json F.json] [--sarif F.sarif] [--with-tests]`.

## Configuration

| Setting | Where | Effect |
|---------|-------|--------|
| `bk-ignore: <rule> -- <reason>` | comment on (or above) a line | waives that rule on that line, in every scanner and the hook |
| `bk-ignore-file: <rule> -- <reason>` | comment anywhere in a file | waives that rule for the whole file (fixtures) |
| `.builder-kit.json` | repo root | `{"ignore": {"<rule>\|*": ["<glob>"]}, "why": {...}}`; `"."` matches repo-wide findings |
| `BUILDER_KIT_HOOKS=off` | env | turns every builder-kit hook off |
| `BUILDER_KIT_STOP_CHECKS=off` | env | Stop hook skips the project's typecheck, lint and related tests (builder-kit scanners still run) |
| `BUILDER_KIT_FORMAT=json` | env | scanners print one JSON finding per line (`ship_check` sets it for its scanners) |

A broken `.builder-kit.json` stops the scan with an error instead of silently waiving nothing; the hook never blocks an edit because of it.

## Install

From GitHub:
```bash
claude plugin marketplace add hasanalaaa/builder-kit
claude plugin install builder-kit@builder-kit
```
From a local clone: `claude plugin marketplace add "/path/to/builder-kit"`, then the same install command. Restart Claude Code after installing.

After changes: bump `version` in `plugins/builder-kit/.claude-plugin/plugin.json`, then run `claude plugin marketplace update builder-kit && claude plugin update builder-kit@builder-kit` and restart Claude Code.

## Layout

```
.claude-plugin/marketplace.json
plugins/builder-kit/
  .claude-plugin/plugin.json
  skills/<skill>/SKILL.md            # + references/, scripts/ (each script has a test_*.py), data/ (design-system)
  commands/*.md                      # slash commands
  agents/*.md                        # reviewer agents
  hooks/hooks.json, post_edit.py, stop_gate.py, project_checks.py, session_start.py
                                     # edit-time guardrail, end-of-turn gate (+ project typecheck/lint/tests), session lessons
  lib/bk.py, lessons.py              # shared: file walk, waivers, report (text or JSON); per-repo lessons memory
  tests/test_integrity.py            # cross-checks skills, references, commands, agents, gate registry
  evals/<case>/                      # claude plugin eval suite
action.yml                           # GitHub Action wrapping ship_check
```

## Tests

```bash
make test    # every stdlib self-test: scanners, hook, shared lib, plugin integrity (skills, refs, gate registry)
make lint    # ruff for real defects, shell syntax, manifest JSON
make check   # the builder-kit gate on this repo
```

Behavioral evals live in `plugins/builder-kit/evals/` (see its README): 15 build tasks where Claude writes real files into a scaffolded repo and graders read them (password reset, IDOR, money, safe migrations, SSRF, webhooks, uploads, RTL, accessible forms…), plus 9 single-turn cases. Every build case runs 3 times per arm, with and without the plugin. They call the model, so they run on demand:

```bash
cd plugins/builder-kit && claude plugin eval . --scaffold --allow-tools Write Edit -j 4
```
In CI: the `evals` workflow (manual, needs the `ANTHROPIC_API_KEY` secret).

## Adding a skill

Create `plugins/builder-kit/skills/<name>/SKILL.md` with `name` and `description` frontmatter. Keep long material in `references/` and tools in `scripts/`, each tool with a test. A scanner builds its findings as tuples and ends with `bk.report(findings, "<name>", root)`, which applies waivers and prints text or JSON. Register it in `skills/ship/scripts/ship_check.py` and the scanner table in `skills/ship/references/lifecycle.md` (`make test` fails until both agree). Add an eval case when the skill should fire on a new kind of request. Bump the version and run `claude plugin validate plugins/builder-kit`.
