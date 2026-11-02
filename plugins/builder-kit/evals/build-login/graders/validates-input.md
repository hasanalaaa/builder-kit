---
type: regex
target: { source: file, path: 'app/api/auth/login/route.ts' }
pattern: 'typeof\s+[\w.?\[\]]+\s*!==?\s*["'']string|z\.object|safeParse'
flags: i
---
