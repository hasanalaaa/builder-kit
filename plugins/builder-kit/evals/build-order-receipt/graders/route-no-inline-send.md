---
type: regex
target: { source: file, path: 'app/api/orders/[id]/pay/route.ts' }
pattern: 'sendEmail\('
flags: i
match: not_contains
---
