---
type: regex
target: { source: file, path: 'lib/password-reset.ts' }
pattern: 'used_?at|\bused\b|consumed|delete\s+from|token\w*\s*=\s*null'
flags: i
---
