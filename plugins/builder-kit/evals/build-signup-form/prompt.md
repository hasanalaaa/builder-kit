---
tags: [build, a11y]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Build components/SignupForm.tsx: full name, email, password (at least 12 characters) and an "I agree to the terms" checkbox. Check the fields when the user submits, show what needs fixing, and POST the data as JSON to /api/signup. Write the file.
