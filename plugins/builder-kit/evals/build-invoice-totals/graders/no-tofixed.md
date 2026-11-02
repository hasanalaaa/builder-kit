---
type: regex
target: { source: file, path: 'lib/invoices.ts' }
pattern: 'toFixed|parseFloat'
flags: i
match: not_contains
---
