---
name: recipes
description: Load before writing a file upload, Stripe webhook, owner-scoped CRUD API, Postgres RLS or streaming AI chat route in Next.js/TypeScript. Copy the tested recipe with bk_add.py and adapt it instead of writing from scratch. Triggers: upload, webhook, RLS, chat API.
---

# Recipes

Tested code you copy in and adapt, instead of writing security-critical routes from scratch. Each recipe is a few small files plus its own vitest suite, verified on Next.js 16 App Router + TypeScript strict + `pg` + zod 4. The tests run real Postgres in-process (PGlite), real Stripe signatures, and a fake model SDK, so the parts that usually go wrong (magic bytes, `event.id` dedupe, owner scoping, RLS, abort on disconnect) are proven, not assumed.

| Recipe | Gives you | Standard it implements |
|--------|-----------|------------------------|
| `file-upload` | `POST /api/uploads`: auth, Content-Length + size cap, type from magic bytes, random server name, no traversal | `launch-security` 18, P13 |
| `stripe-webhook` | `POST /api/webhooks/stripe`: raw-body `constructEvent`, paid checkout → credits, `stripe_events` dedupe in the same transaction, migration | `payments-billing` rule 3, `launch-security` P12 |
| `owner-scoped-api` | `/api/notes` CRUD: session, strict zod, every query `and user_id = $n`, 404 for others' rows, one error shape, page size ≤ 100 | `launch-security` 03, 06, P3, P4 |
| `postgres-rls` | Migration with forced owner policies + `withUser()` helper; test proves user B can't read or write user A's rows | `data-design` rule 8, `launch-security` 03 |
| `ai-chat-stream` | `POST /api/chat`: Anthropic SDK stream, auth, rate limit before spend, input caps, `max_tokens`, timeout, abort on disconnect | `ai-features` rules 1–2, `launch-security` B1 |

## Use

```bash
python3 <skill>/scripts/bk_add.py --list
python3 <skill>/scripts/bk_add.py stripe-webhook --dry-run      # see what lands where
python3 <skill>/scripts/bk_add.py stripe-webhook [--dest DIR]   # copy into the project root
```

`bk_add.py` never overwrites: identical files (shared `src/lib/http.ts`, `db.ts`, `auth.ts`, `env.ts`) are skipped, a different existing file is a conflict (exit 1, nothing copied: merge by hand or add into a scratch `--dest` and compare). It prints the packages to install, env vars to set, the test command and the ADAPT notes.

## Rules

1. **Adapt the marked spots, keep the tested parts.** Change what an `ADAPT:` comment or the printed ADAPT list names (resource names, allowlists, limits, the auth provider in `requireUser()`, storage). Do not remove the checks the tests cover.
2. **Run the recipe's tests after adapting** (`npx vitest run <test files>` and `npx tsc --noEmit`). Rename them along with the code; a red test means the adaptation broke a guarantee.
3. **Match the project.** If it already has an auth helper, DB client or error handler, point the recipe at those instead of adding a second copy. No `src/` dir: drop the prefix and fix the `@/` alias.
4. **Secrets only from server env vars.** `requireUser()` fails closed (401) until wired to a real session.
5. Then run the matching scanners (`launch-security`, `ai-features`, `data-design`) as their skills say.
