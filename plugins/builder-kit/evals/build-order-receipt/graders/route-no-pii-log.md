---
type: regex
target: { source: file, path: 'app/api/orders/[id]/pay/route.ts' }
pattern: '(console|logger)\.\w+\([^)]*(\.|\{\s*|,\s*)(customer_)?email\b'
flags: i
match: not_contains
---
