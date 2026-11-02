---
type: regex
target: { source: file, path: 'migrations/002_plan_and_display_name.sql' }
pattern: 'add\s+column\s+(if\s+not\s+exists\s+)?display_name\s+\w+\s+not\s+null(?![^,;]*default)'
flags: i
match: not_contains
---
