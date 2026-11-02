---
tags: [build, security, auth]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Add email and password sign-in: app/api/auth/login/route.ts (POST { email, password }) checks the password against users.password_hash with bcryptjs, creates a session with lib/session.ts and sets it as a cookie. Follow the existing code. Write the file.
