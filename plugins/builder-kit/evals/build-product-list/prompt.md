---
tags: [build, api]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Add app/api/products/route.ts with a GET for the storefront: it returns products, optionally filtered by ?category=, paginated so the frontend can keep loading more as the shopper scrolls. Write the file.
