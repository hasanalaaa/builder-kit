---
tags: [build, data, payments]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Add invoicing. Write migrations/002_invoices.sql creating invoices and invoice_lines (each line has a description, a quantity and a unit price; an invoice has a subtotal, 15% VAT and a total), and lib/invoices.ts exporting computeTotals(lines) and createInvoice(customerId, lines), which saves an invoice with its lines. Write the files.
