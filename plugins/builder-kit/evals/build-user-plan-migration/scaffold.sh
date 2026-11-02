#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'lib' 'migrations'
cat > 'package.json' <<'J'
{ "name": "saas", "private": true, "dependencies": { "next": "16.0.0", "pg": "8.13.0" } }
J
cat > 'lib/db.ts' <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// production: users has ~4M rows; deploys are rolling (old and new app versions run side by side)
J
cat > 'migrations/001_init.sql' <<'J'
create table users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);
J
cat > 'lib/users.ts' <<'J'
import { pool } from "@/lib/db";
export async function createUser(email: string) {
  const { rows } = await pool.query("insert into users (email) values ($1) returning id", [email.toLowerCase()]);
  return rows[0].id as string;
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
