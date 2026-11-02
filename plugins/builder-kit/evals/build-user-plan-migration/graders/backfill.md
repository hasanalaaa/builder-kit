---
type: regex
target: { source: file, path: 'migrations/002_plan_and_display_name.sql' }
pattern: 'update\s+users\b[^;]*display_name'
flags: i
---
