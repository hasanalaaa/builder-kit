---
tags: [build, payments]
runs: 1
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Users buy credit packs with Stripe Checkout (metadata has userId and credits). Create app/api/webhooks/stripe/route.ts that adds the credits to the user when the payment completes, plus any SQL migration it needs in migrations/. Write the files.
