# Launch security: AUDIT workflow and final report

## 4. AUDIT mode: the full workflow

Follow this order. Do not skip steps. Track progress with the task list.

**Step 0: Safety checkpoint.** Confirm the work is on a branch or the code is committed, so it can be rolled back. If the app is already live with real users, work on a branch/preview and warn before any user-visible change.

**Step 1: Project context.** Gather (from code first, then ask only for what you can't determine): what the app does, who uses it, how it was built, stack, hosting, auth provider, user roles, sensitive data handled, launch status, user's concerns. Write it at the top of `SECURITY_MAP.md`.

**Step 2: Map the app (check 00).** Follow `references/review-and-report.md` §00. Produce `SECURITY_MAP.md`. No code changes in this step. End with the top 5 concerns, ranked, each mapped to a check number.

**Step 2b: Automated sweep.** Run `scripts/security_scan.py <repo>` and `scripts/find-secrets.sh <build-output>`, plus the stack's dependency audit (21) and, if installed, gitleaks (24) and Semgrep. Every ERROR becomes a finding; read the code to confirm each one before acting.

**Step 3: Red flags first.** If any of these is true, fix it before anything else:
- A secret key (OpenAI, Stripe secret, etc.) appears in front-end code → 02, 25
- Supabase/Firebase with no RLS policies or security rules → 03
- Changing an ID in the URL shows someone else's data → 03
- Admin page "protected" only by hiding the link → 09
- App trusts a price or total from the browser → 19
- Orders/plans unlock on the success page instead of a webhook → 19
- A `.env` file was ever committed → 24, 25
- `https://<domain>/.env` returns anything except 404 → 23, 25
- An AI endpoint has no login or usage limit → 12, B1, B5
- Stack traces or SQL errors visible on the live site → 20

**Step 4: Priority eight.** Short on time? Do these in order: 02 → 11 → 24 → 25 → 03 → 01 → 09 → 19.

**Step 5: All remaining checks 01–25** in numeric order, one at a time, each with Audit → Fix → Verify → Done when → Finish-with table. Mark a check N/A only with a stated reason (e.g. "no upload features found: searched X, Y"). Never mark a Critical check N/A without evidence.

**Step 6: Bonus checks B1–B7** where applicable.

**Step 6b: Advanced hardening H1–H16** (`advanced-hardening.md`). Mandatory at ASVS L2/L3. Mark each one Done / N/A with a reason / Open.

**Step 6c: Platform checks** (`platforms.md`) for every non-web surface found in SKILL.md §0.

**Step 6d: Store compliance S1–S10** (`store-compliance.md`) for any App Store / Google Play app. Re-check current store guidelines before submission.

**Step 6e: Automate it** (H13): add CI steps for secrets scan, dependency audit, SAST, the check-27 tests and a DAST baseline on staging, so protection doesn't decay after launch.

**Step 7: Full review (check 26).** Attacker-minded pass across everything, including business-logic flaws. Write `SECURITY_REVIEW.md`. Then **stop and wait for the user's go-ahead** before fixing review findings; after approval fix in severity order and update status.

**Step 8: Prove it (check 27).** Write real, repeatable "try to break it" tests in the project's test framework for every applicable protection; fix failures and re-test; write `SECURITY_REPORT.md` covering all 27 checks. Recommend running the tests in CI on every push.

**Step 9: Lock in the rules.** Offer to add a short security section to the project's `CLAUDE.md` / AI rules file so future code follows SKILL.md §2 (e.g. "Every API route calls `requireUser()` and validates input with Zod. No secret keys in client code. Never trust client prices. Every new table gets RLS policies. Ask before adding packages.").

**Honest note to give the user:** this raises the baseline a lot, but it is not a guarantee. If the app handles payments, health data, children's data or many users, also get a professional security review or penetration test before launch.

---

## 5. What a trustworthy final report looks like

`SECURITY_REPORT.md` must have: the SKILL.md §0 classification (surfaces + ASVS level); every one of the 27 checks listed (including N/A ones), plus every applicable B, H, P and S check; evidence for every "Passed" (test name or command); specific next steps for open items; a checklist of manual actions only the user can do.

Push back on (and never produce): "everything looks secure!" with no evidence; tests deleted or weakened to pass; findings without file, line or endpoint; Critical items quietly marked N/A.
