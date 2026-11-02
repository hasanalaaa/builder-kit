---
type: regex
target: { source: file, path: 'app/api/orders/[id]/route.ts' }
pattern: 'z\.object|safeParse|typeof\s+[\w.?\[\]]+\s*!==?\s*["'']string'
flags: i
---
