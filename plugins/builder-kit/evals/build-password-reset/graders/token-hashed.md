---
type: regex
target: { source: file, path: 'lib/password-reset.ts' }
pattern: 'createHash\(|subtle\.digest|sha256|hashToken|token_hash|tokenHash'
flags: i
---
