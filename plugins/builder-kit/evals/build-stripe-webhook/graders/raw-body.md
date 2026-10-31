---
type: regex
target: { source: file, path: app/api/webhooks/stripe/route.ts }
pattern: 'req(uest)?\.text\(\)|arrayBuffer\(\)'
flags: i
---
