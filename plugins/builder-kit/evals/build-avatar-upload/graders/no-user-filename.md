---
type: regex
target: { source: file, path: app/api/profile/avatar/route.ts }
pattern: '\${?file\.name|\+ ?file\.name'
match: not_contains
---
