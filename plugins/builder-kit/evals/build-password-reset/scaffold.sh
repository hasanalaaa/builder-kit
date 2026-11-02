#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'lib' 'migrations'
cat > 'package.json' <<'J'
{ "name": "accounts", "private": true, "dependencies": { "next": "16.0.0", "pg": "8.13.0", "bcryptjs": "3.0.2" } }
J
cat > 'lib/db.ts' <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// tables: users(id uuid pk, email text unique not null, password_hash text not null)
J
cat > 'lib/mail.ts' <<'J'
export async function sendEmail(to: string, subject: string, html: string) {
  const res = await fetch("https://api.mailer.example/send", {
    method: "POST",
    headers: { authorization: `Bearer ${process.env.MAILER_KEY}`, "content-type": "application/json" },
    body: JSON.stringify({ to, subject, html }),
  });
  if (!res.ok) throw new Error(`mailer ${res.status}`);
}
J
cat > 'migrations/001_init.sql' <<'J'
create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null
);
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
