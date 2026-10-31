---
name: ai-workflow
description: Load at the start of an AI-assisted project or when the AI keeps breaking things or looping. CLAUDE.md/AGENTS.md, plan→small verified steps, checkpoints, reviewing AI diffs, recovery. Triggers: vibe coding, Cursor/Lovable/Bolt, the AI broke my app, الذكاء يخرب الكود.
---

# AI Workflow

AI agents write code fast and confidently, including the wrong code. The difference between a vibe-coded mess and a professional build is not the model: it's the workflow around it. Give the agent the right context, ask for one small thing, verify it actually works, commit, repeat. Never let a session accumulate unreviewed, untested changes.

| File | Use it for |
|------|-----------|
| `references/playbook.md` | Context files, the build loop, prompt patterns and a prompt library, reviewing AI diffs, loop-breaking, recovery with git, parallel work, hooks and guardrails, context/cost hygiene, tool-specific notes (Claude Code, Cursor, Lovable/Bolt/v0, Replit) |
| `scripts/context_pack.py` | Read a repo and print the facts an agent needs (stack, package manager, run/test/lint/build commands, directories, entry points, env var names, docs present) as a draft `CLAUDE.md` "Per-project facts" block |

## 1. Rules

1. **Context before code.** Every project has a `CLAUDE.md`/`AGENTS.md` with stack, exact commands, structure, contracts, traps, and never-touch list (global CLAUDE.md §10). Draft it with `python3 <skill>/scripts/context_pack.py .`, then correct it by hand. Plus `SPEC.md`, `ARCHITECTURE.md`, `DESIGN.md` from the other skills.
2. **One slice per request.** A request should produce a diff you can review in a few minutes: one feature slice, one bug, one refactor step. "Build the whole app" produces a tangle.
3. **Plan, then execute.** For anything non-trivial: ask for a plan (files to touch, approach, risks, tests), correct it, then implement. Plans are cheap to fix; diffs are not.
4. **Verify, don't trust.** The agent runs the app/tests/scanners and shows the output. "It should work" is not a result. You look at the UI yourself for UI changes.
5. **Commit after every green step.** Checkpoints make every mistake a one-command revert. Never start a new step on top of an unverified one.
6. **Two strikes, then re-diagnose.** If the same fix fails twice, stop patching: revert to the last green commit, reproduce, read the actual error and code, form a new hypothesis (`debugging`).
7. **The agent never weakens tests, removes validation or disables security to make something pass.** Treat any such diff as a rejection.
8. **Guardrails run automatically**: builder-kit hooks scan edited files; `ship-check` before merge; CI on every push.
9. **Keep sessions focused.** New task → new session (or clear context). Long sessions drift; summaries lose detail.
10. **You own the result.** Read every diff that touches auth, money, data deletion, permissions or migrations line by line.

## 2. The build loop (every step)

```
1. Pick the next slice from SPEC.md (or the bug).
2. Ask for a plan → review → adjust.
3. Implement the smallest version + its tests.
4. Agent runs: tests, typecheck, lint, builder-kit scanners; you check the UI.
5. Review the diff (playbook.md §4 checklist).
6. Commit with a clear message. Update SPEC/ARCHITECTURE/DESIGN if structure changed.
7. Next slice.
```

## 3. When things go wrong

| Symptom | Do |
|---------|-----|
| Agent loops on the same error | Stop. `git diff` / revert to last green. Paste the exact error + relevant code. Ask for the root cause first, no code. |
| Huge diff touching unrelated files | Reject. Revert. Re-ask with explicit scope ("only change X in file Y"). |
| Something broke, unclear when | `git bisect run <test>` between last known good and now (`debugging`). |
| App "works" but code is messy | `project-architecture` UNTANGLE/SIMPLIFY in small steps. |
| Inherited AI-built app | `project-rescue`. |
| Agent claims done without proof | Ask for the command output / screenshot. Run it yourself. |

## 4. Done when (per session)

- [ ] Every change is committed in small green steps with messages.
- [ ] Tests, typecheck, lint and builder-kit scanners ran and passed (output seen).
- [ ] UI changes looked at in the browser/simulator.
- [ ] Context files updated when structure, commands or decisions changed.
