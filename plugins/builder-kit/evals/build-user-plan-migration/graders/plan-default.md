---
type: regex
target: { source: file, path: 'migrations/002_plan_and_display_name.sql' }
pattern: 'plan\b[^;]*?default\s+''free'''
flags: i
---
