---
type: regex
target: { source: file, path: 'app/api/auth/forgot-password/route.ts' }
pattern: 'status:\s*404|["''`][^"''`\n]*(not found|no account|no user|does not exist|doesn''t exist|unknown email)'
flags: i
match: not_contains
---
