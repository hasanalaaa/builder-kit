---
type: regex
target: { source: file, path: 'migrations/002_plan_and_display_name.sql' }
pattern: 'check\s*\(\s*plan\s+in|create\s+type\b|references\s+plans\b'
flags: i
---
