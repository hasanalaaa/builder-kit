#!/usr/bin/env python3
"""Self-test for schema_check. Run: python3 test_schema_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema_check  # noqa: E402

BAD_1 = """
create table orders (
  id serial,
  user_id uuid references users(id),
  total_amount float,
  placed timestamp
);
create function f() returns void as $$ begin perform 1; end; $$ language plpgsql;
"""
BAD_2 = """
alter table orders add column status text not null;
alter table orders add constraint orders_user_fk foreign key (user_id) references users(id);
alter table orders rename column placed to placed_at;
create index orders_status_idx on orders (status);
drop table legacy;
"""
BAD_PRISMA = """
datasource db { provider = "postgresql" url = env("DATABASE_URL") }
model Payment {
  ref     String
  amount  Float
  paidAt  DateTime
  userId  String
  user    User @relation(fields: [userId], references: [id])
}
"""
GOOD_SQL = """
create table orgs (id uuid primary key default gen_random_uuid(), created_at timestamptz not null default now());
create table invoices (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs(id) on delete cascade,
  total_cents bigint not null check (total_cents >= 0),
  paid_at timestamptz,
  created_at timestamptz not null default now()
);
create index invoices_org_id_idx on invoices(org_id);
"""
GOOD_PRISMA = """
datasource db { provider = "postgresql" url = env("DATABASE_URL") }
model Invoice {
  id         String   @id @default(uuid())
  orgId      String
  totalCents Int
  createdAt  DateTime @default(now()) @db.Timestamptz(3)
  org        Org      @relation(fields: [orgId], references: [id], onDelete: Cascade)
  @@index([orgId])
}
"""


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in schema_check.run(d)[0]}


def test_bad():
    got = run_on({"migrations/001_init.sql": BAD_1, "migrations/002_change.sql": BAD_2, "prisma/schema.prisma": BAD_PRISMA})
    want = {"table-no-pk", "money-float", "naive-timestamp", "no-created-at", "fk-no-index", "fk-no-on-delete",
            "not-null-no-default", "fk-not-valid", "breaking-change", "index-not-concurrent", "drop-table"}
    assert want <= got, sorted(want - got)


def test_good():
    got = run_on({"supabase/migrations/001.sql": GOOD_SQL, "prisma/schema.prisma": GOOD_PRISMA})
    assert not got, sorted(got)


if __name__ == "__main__":
    test_bad()
    test_good()
    print("selftest OK")
