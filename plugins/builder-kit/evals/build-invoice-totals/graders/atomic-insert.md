---
type: regex
target: { source: file, path: 'lib/invoices.ts' }
pattern: '\bbegin\b|transaction|\.connect\(\)|with\s+\w+\s+as\s*\(\s*insert'
flags: i
---
