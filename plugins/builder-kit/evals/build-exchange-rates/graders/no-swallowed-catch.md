---
type: regex
target: { source: file, path: 'lib/exchange-rates.ts' }
pattern: 'catch\s*(\([^)]*\))?\s*\{\s*\}|catch\s*(\([^)]*\))?\s*\{[^}]*return\s+(null|undefined|1|0|\{\})\s*;?\s*\}'
flags: i
match: not_contains
---
