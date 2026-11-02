---
type: regex
target: { source: file, path: 'app/api/auth/login/route.ts' }
pattern: 'rate.?limit|ratelimit|too many|429|throttle|lockout|attempts'
flags: i
---
