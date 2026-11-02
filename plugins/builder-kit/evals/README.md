# builder-kit evals

Two kinds of cases live here:

- **Question cases** (`a11y-modal`, `ai-chat-streaming`, …): one prompt, graded on the reply. Plain Claude already knows most of these rules, so the with/without delta is small.
- **Build cases** (`build-*`, tag `build`): a tiny Next.js/TypeScript repo is scaffolded, Claude is asked for a feature in plain product language, and graders read the files it wrote. Each prompt hides one or more traps that a careless implementation gets wrong. This is the benchmark that shows what the plugin adds.

## Build cases

| Case | Request | A careless version… |
|---|---|---|
| `build-avatar-upload` | profile photo upload | trusts the client MIME type and file name, has no size cap |
| `build-stripe-webhook` | Stripe Checkout credits | skips signature check or `event.id` dedupe, has no transaction |
| `build-password-reset` | forgot / reset password | stores the plain token, reveals which emails have accounts |
| `build-login` | email + password sign-in | has no rate limit, sets a cookie without `httpOnly`/`secure`/`sameSite`, skips input checks |
| `build-order-detail` | GET/PATCH an order by id | loads or updates any user's order (IDOR), takes an unvalidated body |
| `build-invoice-totals` | invoices with 15% VAT | uses float columns, `toFixed` math, no rounding rule, no transaction, no CHECKs |
| `build-user-plan-migration` | new required columns on a big table | adds `NOT NULL` with no default (fails on existing rows), has no backfill or CHECK |
| `build-product-list` | paginated catalog | has no max page size, no `ORDER BY`, no NaN/negative guard, no next-page info |
| `build-exchange-rates` | outbound rate fetch | has no timeout, ignores `res.ok`, returns `1` from a swallowed catch, has no shape check |
| `build-support-chat` | streaming Claude chat | has no auth, no input cap, no role validation, no abort on disconnect or stop |
| `build-language-toggle` | Arabic/English toggle | leaves `<html lang="en">` with no `dir`, keeps `ml-`/`text-left`, keeps no saved choice |
| `build-signup-form` | sign-up form | has no labels, `aria-invalid`, `aria-describedby`, focus on error, live region or `autoComplete` |
| `build-order-receipt` | receipt email when paid | sends inline instead of via the queue, has no idempotency key, logs the customer's email |
| `build-link-preview` | fetch a pasted URL | allows SSRF: no private-IP/DNS check, no protocol allowlist, follows redirects, no timeout or size cap |
| `build-translate-button` | client calls the paid DeepL API | puts the key in the browser (`NEXT_PUBLIC_`), calls the vendor from the client, has no input cap |

Every case runs 3 times per arm (`runs: 3`). Graders are free: `regex` over a written file, `file_exists`, and `tool_used` on `Write` inputs. There are no judge calls.

## Run

From `plugins/builder-kit`. Build cases need `--scaffold` (it runs each case's `scaffold.sh`, which is code in this repo) and need Claude to write files:

```bash
# full benchmark: with plugin vs without (2 arms x 3 runs x 15 cases = 90 runs)
claude plugin eval . --tag build --scaffold --allow-tools Write Edit -j 4 --max-cost-usd 30 --no-publish

# with-plugin arm only (45 runs, about half the cost), e.g. while editing a skill
claude plugin eval . --tag build --scaffold --allow-tools Write Edit --ablation none -j 4

# one case, once, while working on its graders
claude plugin eval . --case build-link-preview --runs 1 --ablation none --scaffold --allow-tools Write Edit

# everything, question cases included
claude plugin eval . --scaffold --allow-tools Write Edit -j 4
```

Put the target (`.`) before `--tag` and `--allow-tools`, since both take a list. Results go to `evals/results/<timestamp>/` (`aggregate-result.json`, `report.html`). That folder is gitignored, so never commit it.

## Cost and time

These are estimates from the 2026-10-31 build run (`build-avatar-upload` and `build-stripe-webhook`, 1 run per arm, list price, default model):

| | Cost per run | Time per run |
|---|---|---|
| with plugin | $0.17–0.20 | ~30 s |
| without plugin | $0.10–0.15 | ~25 s |

Most new cases write 2–4 files, so budget about 1.5× that:

| Command | Runs | Estimated cost | Time at `-j 1` | Time at `-j 4` |
|---|---|---|---|---|
| full, `--ablation with-without` | 90 | $15–25 | 45–70 min | 15–20 min |
| `--ablation none` | 45 | $8–13 | 25–35 min | 8–10 min |
| one case, `--runs 1 --ablation none` | 1 | $0.20–0.35 | < 1 min | – |

`--max-cost-usd` is a hard ceiling. If it is hit, the run exits 2 with `partial: true`; don't use that run in comparisons. Runs count against your plan or API bill.

## Read the results

- `WITH`, `W/OUT`: mean grader pass rate per case with and without the plugin. `Δ` = WITH − W/OUT, and positive means the plugin helped.
- `NOTES` names the highest-weight failing grader. Each grader name states the defect (`token-hashed`, `no-blind-redirects`, …), so a failure tells you which trap was missed.
- Open `report.html` to see each run's verdicts. Add `--keep-temp` to keep each sandbox and read the code Claude wrote.
- With 3 runs per arm, one run moves a 6-grader case by about 0.06. Don't act on a Δ change smaller than about 0.1 on a single case; look at the suite mean Δ and at graders that fail across all 3 runs.

## Compare releases

Pin everything except the plugin, and save JSON:

```bash
claude plugin eval . --tag build --scaffold --allow-tools Write Edit -j 4 \
  --model <model-id> --json evals/results/build-$(git describe --tags --always).json
```

1. Run on the old release tag and on the candidate, with the same `--model`, the same Claude Code version (`claudeVersion` in the JSON) and the same runs.
2. Compare `aggregates.overallScore` (with-arm) and `aggregates.meanDelta`, then per case `cases[].arms.with[].score`.
3. A release is better when the with-arm score is no worse on every case and higher on at least one, beyond noise. Skip any file with `partial: true` or `skippedPaidGraders`.
4. Put the headline numbers in the CHANGELOG entry: suite score, mean Δ, model, Claude Code version.

## Add a build case

1. `build-<name>/` with `prompt.md` (frontmatter as in the existing cases, `runs: 3`), `case.yaml` (`context.scaffold_script: scaffold.sh`), `scaffold.sh` (writes the fixture repo and commits it) and `graders/*.md`.
2. The prompt asks for a product feature and names the files to write. It never names the trap.
3. Each grader is a JavaScript regex over one written file (or a `tool_used: Write` input). Allow every correct alternative you can think of. `file_exists` only sees files created during the run.
4. Before you spend credits, check it offline. Run the scaffold, hand-write a correct solution and a typical careless one, and apply each grader's regex to both. Every grader must pass on the correct solution, and the careless one must fail at least 2.
