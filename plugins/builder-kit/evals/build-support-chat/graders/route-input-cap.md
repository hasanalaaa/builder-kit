---
type: regex
target: { source: file, path: 'app/api/chat/route.ts' }
pattern: '\.max\(|\.length\s*>|MAX_(?!TOKENS)\w+|slice\(\s*-'
flags: i
---
