---
tags: [build, security]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Add a "Translate" button under each review: components/TranslateButton.tsx is a client component that receives the review text and shows the English translation from DeepL (https://api-free.deepl.com/v2/translate; our key is DEEPL_API_KEY in .env.local). Write the files.
