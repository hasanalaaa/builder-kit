---
type: regex
target: { source: file, path: 'migrations/002_invoices.sql' }
pattern: '(price|subtotal|vat|tax|total|amount)\w*\s+(bigint|integer|int[48]?|numeric|decimal)'
flags: i
---
