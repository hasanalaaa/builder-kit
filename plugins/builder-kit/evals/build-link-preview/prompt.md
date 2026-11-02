---
tags: [build, security]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

When a user pastes a link into a post we show a preview card with the page's title, description and image. Add app/api/link-preview/route.ts (POST { url }) that fetches the page and returns { title, description, image }. Write the file.
