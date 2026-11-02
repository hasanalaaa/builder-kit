---
type: regex
target: { source: file, path: 'emails/receipt.ts' }
pattern: 'Intl\.NumberFormat|toLocaleString|format(Money|Currency|Price|Amount)\w*\('
flags: i
---
