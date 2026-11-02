---
type: regex
target: { source: file, path: 'app/api/chat/route.ts' }
pattern: 'z\.enum|z\.literal|role\s*!==?|\.includes\([\w.]*role'
flags: i
---
