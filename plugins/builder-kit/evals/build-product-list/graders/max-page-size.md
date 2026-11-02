---
type: regex
target: { source: file, path: 'app/api/products/route.ts' }
pattern: 'Math\.min\(|MAX_\w*(SIZE|LIMIT|PAGE)|\.max\(\s*\d+\s*\)|maxLimit|maxPageSize|clamp\('
flags: i
---
