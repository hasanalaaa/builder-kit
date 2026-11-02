-- Stripe webhook idempotency + credit balances.
-- A delivered event is recorded in the same transaction as its side effect: a retry or replay of the same
-- event.id hits the primary key and does nothing.
create table stripe_events (
  event_id text primary key,
  type text not null,
  created_at timestamptz not null default now()
);

-- ADAPT: user_id type and a foreign key to your users table (on delete cascade).
create table credit_balances (
  user_id text primary key,
  credits bigint not null default 0 check (credits >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Server-only tables: RLS on with no policies denies every role except the table owner (the role that ran
-- this migration and that the server connects as), e.g. Supabase's anon/authenticated roles.
alter table stripe_events enable row level security;
alter table credit_balances enable row level security;
