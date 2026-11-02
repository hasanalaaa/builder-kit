---
tags: [build, security, authz]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Customers need an order detail page. Add app/api/orders/[id]/route.ts: GET returns the order, and PATCH lets the customer change the shipping address and add a note while the order is still pending. Follow the existing code. Write the file.
