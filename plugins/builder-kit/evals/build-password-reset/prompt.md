---
tags: [build, security, auth]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Add "forgot password". A user types their email on the login page and gets a link; the link opens a page where they pick a new password. Build the backend: app/api/auth/forgot-password/route.ts (POST { email }) and app/api/auth/reset-password/route.ts (POST { token, password }), with the shared logic in lib/password-reset.ts and any SQL in migrations/. Follow the existing code. Write the files.
