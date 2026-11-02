---
tags: [build, email]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

When an order is paid, the customer should get a receipt email listing the items, quantities and the total. Hook it in where the order gets marked paid (app/api/orders/[id]/pay/route.ts) and put the email content in emails/receipt.ts. Follow the existing code. Write the files.
