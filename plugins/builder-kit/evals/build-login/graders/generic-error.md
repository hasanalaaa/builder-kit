---
type: regex
target: { source: file, path: 'app/api/auth/login/route.ts' }
pattern: 'user not found|no user|wrong password|incorrect password|invalid password|email not found|no account'
flags: i
match: not_contains
---
