-- ADAPT: rename "notes" to your resource; add a FK from user_id to your users table (on delete cascade).
create table notes (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  title text not null check (char_length(title) between 1 and 200),
  body text not null default '' check (char_length(body) <= 10000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Serves the owner-scoped list and its keyset pagination.
create index notes_user_created_idx on notes (user_id, created_at desc, id desc);

-- Access goes through the server (src/features/notes/notes.ts scopes every query by owner). RLS on with no
-- policies denies every role except the table owner the server connects as (e.g. Supabase anon/authenticated).
-- Browser or multi-role DB access: add owner policies instead (postgres-rls recipe).
alter table notes enable row level security;
