---
type: regex
target: { source: file, path: 'app/api/orders/[id]/route.ts' }
pattern: 'update\s+orders\b[^`"'']*?\buser_id\b|user_?id\s*!==?|!==?\s*[\w.?]*user_?id|eq\([\w.]*user_?id'
flags: i
---
