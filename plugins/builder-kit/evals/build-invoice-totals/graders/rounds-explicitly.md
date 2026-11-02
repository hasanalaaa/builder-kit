---
type: regex
target: { source: file, path: 'lib/invoices.ts' }
pattern: 'Math\.(round|floor|ceil|trunc)|BigInt|Decimal|Dinero|Big\('
flags: i
---
