---
type: regex
target: { source: file, path: 'app/api/orders/[id]/route.ts' }
pattern: 'user_?id\s*=\s*\$\d|user_?id\s*!==?|!==?\s*[\w.?]*user_?id|eq\([\w.]*user_?id'
flags: i
---
