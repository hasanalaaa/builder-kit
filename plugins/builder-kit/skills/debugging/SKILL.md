---
name: debugging
description: Find and fix the real cause of bugs systematically instead of guessing - reproduce, minimize, form and test hypotheses, read the actual error and code, bisect (git bisect run), instrument with logs/debugger/traces, check environment differences, fix the root cause once for all callers, and lock it with a regression test. Covers common web/app bug classes (hydration mismatch, CORS, env vars, caching/stale data, auth/session, timezone, race conditions, N+1/slow queries, memory leaks, build/deploy-only bugs, mobile-only and RTL-only bugs) and production debugging. Use for any bug, crash, error message, wrong output, flaky behavior, "works locally but not in production", or when an AI fix loop isn't converging; also خطأ, مشكلة, باق, التطبيق يطيح, ما يشتغل.
---

# Debugging

A bug is a gap between what you believe the code does and what it does. Guessing patches symptoms and spawns new bugs; the systematic loop finds the cause, usually faster. The rule from global CLAUDE.md: reproduce before fixing, and fix the root cause where all callers route through.

| File | Use it for |
|------|-----------|
| `references/methods.md` | The loop in detail, reproduction and minimization, reading errors and stack traces, hypothesis log, bisecting, instrumentation per stack, environment diffing, a catalog of common bug classes with how to confirm and fix each, production debugging, flaky bugs, postmortems |

## 1. The loop

1. **Reproduce.** Exact steps, input, environment, account, browser/device, locale. Make it happen on demand; ideally as a failing automated test.
2. **Read the evidence.** The full error message and stack trace, logs around the request ID, network tab (status, response body), console, server logs. Read the code on the failing path; never infer behavior from names.
3. **Minimize.** Remove everything not needed to trigger the bug: smaller input, fewer steps, one component, one request.
4. **Hypothesize.** Write 2–3 candidate causes with the evidence for each. Pick the most likely and cheapest to test.
5. **Test the hypothesis** with an experiment that can prove it wrong (a log, a breakpoint, a unit test, toggling one variable). Record the result.
6. **Fix the root cause**: in the shared function/module all callers use, not in the one caller from the ticket. Grep for siblings with the same pattern.
7. **Lock it**: the failing test now passes; add tests for sibling cases; run the whole suite.
8. **Explain it** in the commit/PR: cause, fix, why it can't recur (or what guards it).

## 2. Rules

1. No fix without a reproduction (or, for production-only bugs, without evidence pinpointing the cause).
2. Change one thing at a time; revert experiments that disproved a hypothesis.
3. Two failed fixes → stop, revert, re-diagnose from evidence (`ai-workflow` §3).
4. Suspect recent changes first: `git log -p`, deploy history, dependency updates (`git bisect run` when unsure).
5. Compare environments when "works here, not there": env vars, versions, data, region, flags, caches, build mode.
6. Never "fix" by swallowing the error, widening a type to `any`, disabling a check or deleting a test.
7. Leave the code better instrumented if the bug was hard to find (a log line with context, an assertion, an error message that names the cause).

## 3. Done when

- [ ] Root cause stated in one or two sentences with evidence.
- [ ] Fix at the shared point; sibling occurrences checked.
- [ ] Regression test fails before, passes after; full suite green.
- [ ] Temporary logs/debug code removed; useful instrumentation kept.
- [ ] For production incidents: postmortem notes (`observability` §13).
