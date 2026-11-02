---
type: regex
target: { source: file, path: 'migrations/002_invoices.sql' }
pattern: '\b[a-z_]+\s+(real|float[48]?|double\s+precision|money)\s*(,|\)|not\b|null\b|default\b|check\b)'
flags: i
match: not_contains
---
