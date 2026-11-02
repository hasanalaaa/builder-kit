---
type: regex
target: { source: file, path: 'app/api/products/route.ts' }
pattern: '(limit|offset|=|like)\s*''?%?\$\{'
flags: i
match: not_contains
---
