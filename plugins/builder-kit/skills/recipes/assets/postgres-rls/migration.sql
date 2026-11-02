-- Row-level security on plain Postgres: the database itself refuses other owners' rows.
-- The app runs each request in a transaction that sets app.user_id (src/lib/rls.ts withUser) and connects
-- as a role that is a member of app_user: never a superuser or a BYPASSRLS role, which skip RLS.
do $$
begin
  if not exists (select from pg_roles where rolname = 'app_user') then
    create role app_user nologin;
  end if;
end $$;

-- ADAPT: rename "documents"; add a FK from owner_id to your users table.
create table documents (
  id uuid primary key default gen_random_uuid(),
  owner_id text not null default current_setting('app.user_id', true) check (owner_id <> ''),
  title text not null check (char_length(title) between 1 and 200),
  created_at timestamptz not null default now()
);
create index documents_owner_idx on documents (owner_id);

alter table documents enable row level security;
alter table documents force row level security; -- the table owner is bound by the policies too

-- Unset app.user_id is null or '' and matches no row: fail closed.
create policy documents_select on documents for select to app_user
  using (owner_id = current_setting('app.user_id', true));
create policy documents_insert on documents for insert to app_user
  with check (owner_id = current_setting('app.user_id', true));
create policy documents_update on documents for update to app_user
  using (owner_id = current_setting('app.user_id', true))
  with check (owner_id = current_setting('app.user_id', true));
create policy documents_delete on documents for delete to app_user
  using (owner_id = current_setting('app.user_id', true));

grant select, insert, update, delete on documents to app_user;
