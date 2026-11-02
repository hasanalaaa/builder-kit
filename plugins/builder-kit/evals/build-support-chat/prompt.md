---
tags: [build, ai]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Add a support chat for signed-in customers: app/api/chat/route.ts streams Claude's answer to the conversation the browser sends ({ messages: [{ role, content }] }), and components/SupportChat.tsx shows the conversation and renders the reply as it streams in. Follow the existing code. Write the files.
