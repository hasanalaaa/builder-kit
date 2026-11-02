# Orchestration: the right model for each job

One model in one context does everything badly at once: wide reading fills the context, the author reviews its own assumptions, and the strongest model is paid to grep. Split the work by what it needs.

| Job | Who | Why |
|-----|-----|-----|
| Plan, mini spec, slice split, merge, decisions | Main thread (the user's model) | Needs the conversation and the user's OK; keeps the decisions in one place |
| Wide reading: "where is X, what calls Y" | `builder-kit:explorer` (haiku, read-only) | Its reading never enters the main context; returns a file:line table |
| Build one independent slice | `builder-kit:slice-builder` (sonnet, own worktree) | Parallel and isolated; returns diff summary + evidence, not its transcript |
| Review the combined diff | `builder-kit:builder-reviewer` (opus, fresh context) | Sees only the diff, the code it touches and the spec, so it isn't blind to the author's assumptions |
| Review rendered UI | `builder-kit:ui-reviewer` (sonnet) | Screenshots and lints stay out of the main context |

## When to fan out

Fan-out costs tokens: each agent re-reads `CLAUDE.md`, the spec and the files it needs. It pays off only when slices are real and independent.

- **Single-threaded** (build it in the main thread): under 3 files, one slice, slices that share a file, or a cross-cutting change (walking skeleton, rename, schema change everyone depends on).
- **Fan out**: 2+ slices that each own their files and can be tested alone (e.g. API endpoint, UI screen, email template of one feature).
- **Never fan out** on an untested inherited codebase (`project-rescue`): fix sequentially, one verified commit each.

## The flow

```
1. Main: explorer for the map (if needed) → mini spec + slice plan → user OK.
2. Main: commit the plan; note BASE=$(git rev-parse HEAD).
3. Fan out, in parallel, one slice-builder per independent slice:
   base SHA, goal, acceptance criteria, allowed files, out of scope.
4. Main: merge each DONE branch (git merge <branch>); handle BLOCKED here; run the tests.
5. builder-reviewer on BASE..HEAD with the spec only (never the authors' summaries).
6. Fix Critical/High → gate (ship_check --only …, project tests) → commit.
```

## Rules

- **The brief is the contract.** A slice brief names its files and criteria. A slice that needs a file outside its list stops and reports; the main thread re-plans.
- **Base SHA, always.** Subagent worktrees branch from the default branch unless the user set `worktree.baseRef: "head"`; the slice-builder fast-forwards to the given SHA, so the plan must be committed first.
- **Results, not transcripts.** Agents return tables and evidence (commands + output tails). The main thread reads results, not file dumps.
- **The reviewer starts cold.** Pass the range and the spec. A summary like "all tests pass" biases the review; the reviewer verifies it instead.
- **Two failed attempts in a slice → BLOCKED**, not a third guess (`debugging`).
- **Merge conflicts mean the split was wrong.** Resolve in the main thread and split by file ownership next time.
