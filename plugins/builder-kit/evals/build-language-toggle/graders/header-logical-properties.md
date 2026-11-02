---
type: regex
target: { source: file, path: 'components/Header.tsx' }
pattern: '\b(ml|mr|pl|pr)-(\d|auto|px)|\btext-(left|right)\b|\bborder-[lr]\b|\brounded-[lr]\b|\b(left|right)-\d'
flags: i
match: not_contains
---
