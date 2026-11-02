---
tags: [build, data]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Every user now needs a plan ('free' or 'pro'; everyone who exists today is on 'free') and a display name we can show in the UI (existing users start with the part of their email before the @). Both are required from now on. Write migrations/002_plan_and_display_name.sql and update createUser in lib/users.ts to take a display name. Write the files.
