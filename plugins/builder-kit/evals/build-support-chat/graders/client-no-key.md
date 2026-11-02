---
type: regex
target: { source: file, path: 'components/SupportChat.tsx' }
pattern: 'ANTHROPIC_API_KEY|@anthropic-ai/sdk|NEXT_PUBLIC_'
flags: i
match: not_contains
---
