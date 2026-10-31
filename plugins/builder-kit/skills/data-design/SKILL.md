---
name: data-design
description: Database and data-model design for any app - schemas, keys, relations, constraints, indexes, money and time types, multi-tenancy, soft delete, audit trails, safe zero-downtime migrations, query performance (N+1, missing indexes, pagination), backups and data lifecycle. Use when creating or changing tables/collections/models, writing migrations, adding a column, designing relations, choosing IDs, seeing slow queries, or planning data for a new feature. Works with Postgres/Supabase, MySQL, SQLite, Prisma, Drizzle, SQLAlchemy, Django ORM. Also for قاعدة البيانات, الجداول, مايقريشن, تصميم البيانات, الاستعلامات بطيئة. Ships schema_check.py that flags missing primary keys, unindexed foreign keys, float money, naive timestamps and unsafe migrations.
---

# Data Design

Data outlives code. A bad function is fixed in a commit; a bad schema with a year of production rows is fixed with migrations, backfills and downtime. Decide the data model for the long term (global CLAUDE.md §0: longevity wins at the boundaries).

| File | Use it for |
|------|-----------|
| `references/schema.md` | Modeling rules, IDs, types (money, time, enums, JSON), constraints, relations, multi-tenancy, soft delete, audit, naming, Postgres/Supabase specifics, a reference schema |
| `references/migrations-and-queries.md` | Zero-downtime migration patterns (expand → migrate → contract), backfills, locking hazards, indexes, N+1, pagination, transactions, concurrency, caching, backups and restore drills |
| `scripts/schema_check.py` | Scan `.sql` migrations and `schema.prisma` for missing PKs, unindexed FKs, float money, naive timestamps, missing `created_at`, NOT NULL without default, destructive changes, non-concurrent indexes, missing ON DELETE |

## 1. Rules

1. **Model the domain, not the screen.** Entities and their relationships from `SPEC.md` §Data; screens change, entities rarely do.
2. **The database enforces the truth.** NOT NULL, UNIQUE, CHECK, foreign keys, enums or check-constrained text. App validation is for messages; constraints are for correctness. Two app servers racing will break any invariant that only lives in code.
3. **Every table has**: a primary key, `created_at timestamptz not null default now()`, `updated_at` when rows change, and an owner column when rows belong to a user or tenant (`user_id`, `org_id`).
4. **Money is integer minor units** (`amount_cents bigint`) or `numeric(19,4)`, plus a `currency char(3)`. Never float.
5. **Time is `timestamptz` in UTC.** Store instants in UTC, convert at display with the user's time zone. Dates without time (birthdays, due dates) are `date`.
6. **Index what you filter, join and sort on.** Every foreign key gets an index (Postgres doesn't create one). Composite indexes match the query's equality columns first, then range/sort.
7. **Migrations are forward-only, reviewed and reversible in practice.** Never edit a migration that has run anywhere shared. Breaking changes use expand → migrate → contract.
8. **Access control lives next to the data** when the client can reach the DB (Supabase/Firebase): RLS on every table (`launch-security` 03). Otherwise one data-access module per feature owns its tables.
9. **Delete deliberately.** Decide per entity: hard delete, soft delete (`deleted_at`), or archive. Account deletion must really remove or anonymize personal data (`legal-compliance`, store rules).
10. **Backups are only real when restored.** Point-in-time recovery on, and a restore drill on a schedule (`launch-security` B3).

## 2. Workflow: new feature or table

1. Read `SPEC.md` (data, roles, retention) and existing schema. Search for an existing table that already models the concept before adding one.
2. Sketch: entities, relationships (1:1, 1:N, N:M via join table), ownership, lifecycle (states and transitions), volume estimate (rows/day), read patterns (the 3–5 queries the feature runs).
3. Write the schema with `schema.md` rules: types, constraints, indexes for the read patterns, RLS/policies.
4. Write the migration (`migrations-and-queries.md` §1). For changes to existing tables, plan the zero-downtime steps.
5. Run `python3 <skill>/scripts/schema_check.py .` → 0 ERROR. For Supabase also run `launch-security/scripts/security_scan.py` (RLS check).
6. Write the data-access functions (one module per feature, `project-architecture` law 3). Check every list query for N+1 and pagination.
7. Test: constraints reject bad data, owner scoping (user A can't see B), migration runs on a copy of production-like data.
8. Update `ARCHITECTURE.md` data section / ER diagram (Mermaid `erDiagram`).

## 3. Workflow: slow query or data bug

1. Reproduce with real-ish volume. Get the query plan: `EXPLAIN (ANALYZE, BUFFERS)` on Postgres; Supabase/Neon dashboards show slow queries (`pg_stat_statements`).
2. Look for: sequential scans on large tables, N+1 (many identical queries per request), OFFSET pagination on deep pages, missing composite index, functions on indexed columns (`lower(email)` needs an expression index), implicit casts.
3. Fix the cause (index, query shape, batching), measure again, keep the plan in the PR.

## 4. Done when

- [ ] `schema_check.py` 0 ERROR; every WARN fixed or explained.
- [ ] Every table: PK, timestamps, owner column where applicable, constraints for invariants, indexes for its read patterns and FKs.
- [ ] RLS/policies or a single data-access module guards every table.
- [ ] Migration tested on realistic data; breaking changes split into expand/contract.
- [ ] List endpoints paginate; no N+1 in the feature's requests.
- [ ] Retention and deletion behavior decided and implemented.
- [ ] ER diagram / data section updated.
