---
type: regex
target: { source: file, path: 'components/TranslateButton.tsx' }
pattern: 'DEEPL_API_KEY|NEXT_PUBLIC_|DeepL-Auth-Key'
flags: i
match: not_contains
---
