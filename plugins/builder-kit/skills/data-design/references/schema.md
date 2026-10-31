# Schema design

## 1. Identifiers

| Option | Use when | Notes |
|--------|----------|-------|
| `bigint generated always as identity` | Internal tables, joins, high volume | Small, fast, ordered. Don't expose sequential IDs where enumeration matters |
| `uuid` (v7 preferred, v4 ok) | IDs exposed in URLs/APIs, client-generated IDs, merging data, Supabase default | v7 is time-ordered → better index locality. `gen_random_uuid()` is v4 |
| Public slug / short ID | Human-facing URLs | Separate unique column; never the only key |

Never use email, phone or name as a primary key. Never `serial` on new Postgres tables (identity is the standard).

## 2. Types

| Data | Type | Avoid |
|------|------|-------|
| Money | `bigint` minor units (`price_cents`) + `currency char(3)`; or `numeric(19,4)` | `float`, `real`, `double precision`, JS `number` math on decimals |
| Instant | `timestamptz` (stored UTC) | `timestamp` without time zone, local time strings |
| Calendar date | `date` | timestamp at midnight |
| Duration | `interval` or integer seconds | strings |
| Enum-like state | `text` + `CHECK (status in (...))` or Postgres `enum` (harder to change) | free text |
| Boolean flags | `boolean not null default false` | nullable booleans (three states) |
| Email | `text` with lower-cased unique index (`citext` or `unique (lower(email))`) | case-sensitive uniqueness |
| Phone | `text` in E.164 (`+9665…`) | integers |
| Free-form attributes | `jsonb` for genuinely unstructured data, with a CHECK or app schema | jsonb for core relational fields you filter on |
| Arabic text | `text` (UTF-8); search with normalization (alef/hamza/taa marbuta/diacritics) | `varchar(n)` too short for Arabic expansion |
| Files | storage path/key + metadata columns | blobs in the main DB |
| Geography | PostGIS `geography(Point)` | separate lat/lng floats if you need distance queries |

## 3. Constraints

- `NOT NULL` by default; nullable only when "unknown" is a real state.
- `UNIQUE` for natural uniqueness (one membership per user per org: `unique (org_id, user_id)`).
- `CHECK` for ranges and states (`quantity > 0`, `ends_at > starts_at`).
- Foreign keys with explicit `ON DELETE`: `cascade` for owned children (order items), `restrict` for references that must not vanish (invoice → customer), `set null` for optional links.
- Partial unique indexes for soft delete: `unique (email) where deleted_at is null`.
- Exclusion constraints for no-overlap bookings (Postgres `EXCLUDE USING gist`).

## 4. Relations

- 1:N → FK on the child + index.
- N:M → join table with composite PK `(a_id, b_id)` + index on `(b_id)`; add columns (role, created_at) when the link has data.
- Polymorphic "belongs to anything" (`target_type`, `target_id`) breaks FKs; prefer separate nullable FKs with a CHECK that exactly one is set, or separate tables.
- Hierarchies: `parent_id` (adjacency) + recursive CTE for small trees; `ltree` or closure table for deep/large trees.

## 5. Multi-tenancy

- Default: shared tables with `org_id` on every tenant-owned row, enforced by RLS (`org_id in (select org_id from memberships where user_id = auth.uid())`) or by a data-access layer that always scopes.
- Composite indexes start with `org_id`.
- Unique constraints include `org_id` (`unique (org_id, slug)`).
- Never trust `org_id` from the client body; derive it from the session/membership.
- Separate schemas/databases per tenant only for strict isolation/compliance needs.

## 6. Lifecycle, audit, history

- State machines: `status` column with CHECK, plus timestamp columns for key transitions (`paid_at`, `shipped_at`). Enforce valid transitions in one function.
- Soft delete: `deleted_at timestamptz`; every query and RLS policy filters it; partial indexes; a purge job for retention.
- Audit log table for sensitive changes: `who, action, entity, entity_id, before jsonb, after jsonb, at, ip` (append-only; launch-security 08).
- Optimistic concurrency: `version int` or `updated_at` check in UPDATE ... WHERE to prevent lost updates.
- Idempotency: `unique (idempotency_key)` on tables written by retries/webhooks.

## 7. Naming

- `snake_case`, plural table names (`orders`), singular column names, `<entity>_id` for FKs, `is_`/`has_` for booleans, `_at` for timestamps, `_cents`/`_minor` for money.
- Join tables: `<a>_<b>` (`project_members`).
- Indexes: `<table>_<cols>_idx`; unique: `<table>_<cols>_key`.

## 8. Postgres / Supabase specifics

- Enable RLS on every table in an exposed schema; write policies for select/insert/update/delete separately with `(select auth.uid())` (cached per statement).
- Put privileged logic in `security definer` functions with `set search_path = ''`, owned by a role without login.
- Use `public` only for app tables; keep internal tables in a non-exposed schema.
- Generated columns for derived values (`full_name`, search vectors).
- Full-text search: `tsvector` generated column + GIN index; for Arabic use a normalization function (strip diacritics, unify alef forms) before indexing, or a dedicated search engine.
- `pg_stat_statements` on; check slow queries weekly.

## 9. Reference schema (SaaS with orgs)

```sql
create table orgs (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(name) between 1 and 120),
  created_at timestamptz not null default now()
);
create table memberships (
  org_id uuid not null references orgs(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner','admin','member')),
  created_at timestamptz not null default now(),
  primary key (org_id, user_id)
);
create index memberships_user_id_idx on memberships(user_id);
create table invoices (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs(id) on delete cascade,
  number text not null,
  status text not null default 'draft' check (status in ('draft','sent','paid','void')),
  total_cents bigint not null check (total_cents >= 0),
  currency char(3) not null default 'SAR',
  due_on date,
  paid_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, number)
);
create index invoices_org_id_status_idx on invoices(org_id, status, created_at desc);
alter table invoices enable row level security;
create policy invoices_member_select on invoices for select
  using (org_id in (select org_id from memberships where user_id = (select auth.uid())));
```
