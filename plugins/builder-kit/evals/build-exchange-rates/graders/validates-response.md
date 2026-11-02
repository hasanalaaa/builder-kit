---
type: regex
target: { source: file, path: 'lib/exchange-rates.ts' }
pattern: 'typeof\s+[\w.?\[\]]+\s*!==?\s*["'']number|Number\.isFinite|isFinite\(|isNaN|z\.|safeParse'
flags: i
---
