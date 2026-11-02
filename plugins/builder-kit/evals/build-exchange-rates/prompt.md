---
tags: [build, errors]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Checkout shows prices in the shopper's currency. Add lib/exchange-rates.ts exporting getRate(from, to), which gets the rate from https://api.frankfurter.app/latest?from=USD&to=EUR (the response looks like { "rates": { "EUR": 0.92 } }), and app/api/rates/route.ts (GET ?from=&to=) that returns { rate }. Write the files.
