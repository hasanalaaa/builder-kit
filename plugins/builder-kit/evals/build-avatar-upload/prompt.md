---
tags: [build, security]
runs: 1
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Add profile photo upload: create app/api/profile/avatar/route.ts (POST, multipart form field "file") that stores the image in Supabase Storage and saves its path on the user's profile. Follow the existing code. Write the file.
