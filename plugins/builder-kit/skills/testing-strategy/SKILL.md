---
name: testing-strategy
description: Decide what to test and how, then prove features work - test pyramid/trophy per stack, unit/integration/E2E/contract/visual/accessibility tests, acceptance criteria to tests, abuse and failure-path tests, fixtures and factories, network mocking (MSW), Playwright E2E, flaky-test control, CI gates and coverage that means something. Use when adding a feature, fixing a bug (write the failing test first), setting up testing in a new project, when tests are missing, flaky or slow, or when the user says test, tests, QA, TDD, coverage, E2E, Playwright, Vitest, Jest, pytest, اختبار, اختبارات, تأكد إنه يشتغل. Ships audit_tests.py (focused/skipped tests, sleeps, empty assertions, untested modules, missing test setup).
---

# Testing Strategy

Tests are how a vibe-coded app becomes a product: they turn "it worked when I tried it" into "it keeps working after every change, including the ones the AI makes at 2am". Test behavior the user and the spec care about, at the cheapest level that proves it.

| File | Use it for |
|------|-----------|
| `references/playbook.md` | Levels and what each proves, the testing shape per stack, tools, acceptance criteria → tests, abuse/failure tests, fixtures/factories, mocking, E2E rules, flakiness, CI, coverage, AI-specific rules, setup snippets |
| `scripts/audit_tests.py` | Audit a repo's tests: no tests, no test script, `.only`/`fit` committed, skipped tests, `sleep`/`waitForTimeout`, tests without assertions, trivially true assertions, source modules with no test |

## 1. Rules

1. **Acceptance criteria become tests.** Every Given/When/Then line in the spec (`product-spec`) maps to at least one automated test.
2. **Bugs start with a failing test.** Reproduce in a test, watch it fail, fix, watch it pass. A fix without a test regresses.
3. **Test behavior through public interfaces**, not implementation details: HTTP endpoints, exported functions, rendered UI by role/label. Refactors shouldn't break tests.
4. **Cheapest level that proves it.** Pure logic → unit. Handler + DB + auth → integration (real DB in a container or a test schema). Critical user journeys → a few E2E. Don't E2E what an integration test proves.
5. **Unhappy paths are first-class**: invalid input, unauthorized (401), other user's resource (403/404), conflicts, dependency down/timeouts, empty states, limits (`launch-security` 27, H2–H7; `error-handling`).
6. **Deterministic or deleted.** No real network to third parties, no sleeps, controlled time and randomness, isolated data per test. A flaky test is quarantined and fixed within days.
7. **Never weaken a test to make it pass.** Decide whether the code or the test is wrong and say which (global CLAUDE.md §7).
8. **Tests run on every push in CI** and block merge. Fast tests locally (< 1 min for the unit/integration suite is a good target).
9. **Coverage is a flashlight, not a goal.** Use it to find untested critical code (auth, money, permissions, data writes); require high coverage there, not everywhere.

## 2. Workflow: new project

1. Pick tools from `playbook.md` §3 for the stack. Add the `test` script to `package.json` / `pyproject` / Makefile.
2. Write the first integration test in the walking skeleton (Slice 0): one endpoint, one DB row, auth stub.
3. Add Playwright with one smoke E2E (home loads, sign in, main action).
4. Wire CI (`deploy-release`): lint → typecheck → unit/integration → E2E on preview → security scan.

## 3. Workflow: each feature or fix

1. List tests from the acceptance criteria + failure modes (§1 rule 5). Write them as a checklist in the PR.
2. Write the failing test(s) first for bugs; for features, write tests alongside the code, slice by slice.
3. Run the suite; then `python3 <skill>/scripts/audit_tests.py .` → 0 ERROR.
4. Review: does each test fail if the behavior breaks? (Temporarily break the code, see it fail.)

## 4. Done when

- [ ] Every acceptance criterion has a test; every bug fix has a regression test.
- [ ] Unhappy paths covered (auth, ownership, validation, dependency failure, empty, limits).
- [ ] No `.only`, no unexplained skips, no sleeps, no real third-party calls (`audit_tests.py` 0 ERROR).
- [ ] Suite passes locally and in CI; E2E covers the critical journeys.
- [ ] Critical modules (auth, payments, permissions, data writes) have high coverage.
