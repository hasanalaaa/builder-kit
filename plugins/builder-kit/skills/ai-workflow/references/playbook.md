# AI workflow playbook

## 1. Context files

**Project `CLAUDE.md` / `AGENTS.md`** (Cursor: `.cursor/rules/*.mdc`; Copilot: `.github/copilot-instructions.md`; Lovable/Bolt: project knowledge field). Keep it short and factual:
```markdown
# Project facts
- Stack: Next.js 15 (App Router) · TypeScript strict · Tailwind v4 · Supabase (Postgres, Auth, Storage) · Stripe
- Install: pnpm install · Dev: pnpm dev · Test: pnpm test · E2E: pnpm e2e · Lint: pnpm lint · Typecheck: pnpm typecheck · Build: pnpm build
- Structure: see ARCHITECTURE.md (features in src/features/<name>, each with index.ts front door)
- Design: DESIGN.md (tokens in src/styles/tokens.css; Arabic-first RTL)
- Published contracts: /api/v1/* (mobile app v1.2+ depends on it), Supabase schema, Stripe webhooks
- Known traps: middleware.ts must stay edge-compatible; dates stored UTC, displayed Asia/Riyadh
- Never touch: supabase/migrations already applied, .env*, generated types in src/types/db.ts (run pnpm db:types)
- Standards: builder-kit skills (launch-security, project-architecture, design-system…); run ship-check before merge
```
Generate a draft: `python3 <ai-workflow>/scripts/context_pack.py .` → review → save.

Other context: `SPEC.md` (what), `ARCHITECTURE.md` (where), `DESIGN.md` (how it looks), ADRs (why). Point to them; don't paste them into every prompt.

## 2. Prompt patterns

**Feature slice**
```
Read SPEC.md story S3 and ARCHITECTURE.md. Plan only, no code yet:
- files you'll create/change (follow the nearest sibling feature),
- data/API changes, permissions, states (loading/empty/error),
- tests you'll write from the acceptance criteria.
Keep it to one vertical slice. Wait for my OK.
```
**Implementation after plan**
```
Implement the plan. Smallest version that meets the acceptance criteria.
Then run: pnpm test, pnpm typecheck, pnpm lint, and the builder-kit scanners on the changed files.
Show me the outputs. Don't change files outside the plan.
```
**Bug**
```
Bug: <observed> vs <expected>. Steps: <…>. Error: <exact text>.
First reproduce it with a failing test. Then find the root cause and explain it in 3 lines before changing code.
Fix the cause (not the symptom), keep the test, run the suite.
```
**Refactor**
```
Refactor <module> for <goal> without changing behavior. Tests must stay green and unchanged.
One step at a time; commit-sized steps; list each step first.
```
**UI**
```
Build <screen> per DESIGN.md and design-system patterns.md §<n>. States: loading/empty/error/success/no-permission.
Arabic RTL and English. Then open it at 375 and 1280 px and show me screenshots.
```
**Review**
```
Review this diff as a senior engineer: correctness, security (launch-security §2), structure (project-architecture checklist),
tests, scope creep. List findings by severity with file:line. Don't fix yet.
```
**Explain before touching**
```
Explain how <flow> works today: entry points, files, data, side effects. No changes.
```

Prompt hygiene: one goal per prompt; give file paths; paste exact errors; say what NOT to change; ask for verification output; specify languages (ar/en) and platforms.

## 3. Plan → execute → verify

- Use plan mode (Claude Code) or "plan first" instructions in other tools.
- A good plan names files, functions, data changes, tests and risks. A vague plan ("I'll update the components") means the agent doesn't know yet: ask it to read more code first.
- Verification = commands run + output shown + UI looked at. For UI, use the browser/simulator tools or open it yourself.

## 4. Reviewing AI diffs (checklist)

- [ ] Scope: only files the plan named; no unrelated reformatting/renames; no new dependencies without reason.
- [ ] Reuse: didn't re-create an existing helper/component (`project-architecture` law 6).
- [ ] Correctness: edge cases (empty, null, large, concurrent, failure); error handling (`error-handling`).
- [ ] Security: auth + ownership on endpoints, validation, no secrets, no raw HTML (`launch-security`).
- [ ] Tests: new tests fail without the change; no weakened/deleted assertions; no `.only`/skip.
- [ ] Structure: right folder, front doors respected, no cycles (`arch_check.py`).
- [ ] UI: tokens only, states, RTL, accessibility (`design_lint.py`, `a11y_lint.py`, `rtl_lint.py`).
- [ ] No debug leftovers, commented-out code, TODOs without owner.

## 5. Breaking loops

Signs: the same error after 2 attempts; the agent alternates between two approaches; each fix breaks another test; the diff keeps growing.
Do:
1. Stop and revert to the last green commit (`git stash` or `git restore .` after saving anything useful).
2. Write down the exact failing behavior and error.
3. Ask for diagnosis only: "List 3 hypotheses for the root cause, with evidence from the code for each."
4. Test the most likely hypothesis with a minimal experiment (a log, a unit test).
5. Fix with the understanding; if still stuck, reduce the problem (minimal repro) or ask a human/another model to review.

## 6. Recovery with git

- Checkpoint often: `git add -A && git commit -m "feat(invoices): send invoice email"`.
- Undo uncommitted changes to a file: `git restore <file>`; all: `git restore .` (careful: irreversible for uncommitted work).
- Undo last commit but keep changes: `git reset --soft HEAD~1`.
- Revert a pushed commit safely: `git revert <sha>`.
- Find the breaking commit: `git bisect start; git bisect bad; git bisect good <sha>; git bisect run pnpm test`.
- Work on risky ideas in a branch or worktree (`git worktree add ../app-experiment -b experiment`).
- Lovable/Bolt/Replit: use their history/restore points, and sync to GitHub so you have real git history.

## 7. Parallel work

- Independent tasks (different features/files) can run in parallel sessions/worktrees; never two agents editing the same files.
- Subagents for read-only work: searching the codebase, reviewing a diff, researching docs; main session keeps decisions.
- Merge one branch at a time with CI green.

## 8. Guardrails and hooks

- builder-kit hooks run fast scanners on every edited file and report blocking issues back to the agent (security secrets/injection, design bans, RTL physical properties, empty catches).
- `ship-check` (all scanners + tests summary) before merge/release.
- CI enforces the same (`deploy-release`).
- Permissions: deny destructive commands by default; allow-list common safe commands to reduce prompts.

## 9. Context and cost hygiene

- New task → new session or `/clear`; long sessions compress and lose details.
- Point to files instead of pasting large content; ask the agent to read only what's needed.
- Use cheaper/faster models for search, summaries and simple edits; the strongest for design decisions, tricky bugs and reviews.
- Keep `CLAUDE.md` short (facts, not essays); move long guidance into skills/docs loaded on demand.

## 10. Tool notes

- **Claude Code**: CLAUDE.md hierarchy (global → project → folder), plan mode, skills/plugins (builder-kit), hooks, subagents, worktrees, `/review`, MCP tools for browser/DB/docs.
- **Cursor**: project rules (`.cursor/rules`), agent mode with checkpoints, `@file` context; keep rules in sync with CLAUDE.md (or symlink AGENTS.md).
- **Lovable / Bolt / v0**: great for first UI and prototypes; connect GitHub early; give them the spec and design system; export to a real repo and continue with this workflow when the app grows (`project-rescue` for the handover).
- **Replit Agent**: use checkpoints; keep secrets in Replit Secrets; export to GitHub for CI.
- **Copilot / inline completions**: fine for local code; still review, still test.

## 11. Anti-patterns

- "Build me an app like X" with no spec → generic app with invented features.
- Accepting a 2,000-line diff because it "seems to work".
- Letting the agent delete or skip tests, or add `any`/`@ts-ignore` to silence errors.
- Fixing production by prompting directly against live data.
- Multiple agents editing the same files.
- Never reading the code because "the AI wrote it".
