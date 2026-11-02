#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'lib'
cat > 'package.json' <<'J'
{ "name": "accounts", "private": true, "dependencies": { "next": "16.0.0", "pg": "8.13.0", "bcryptjs": "3.0.2", "zod": "4.1.0" } }
J
cat > 'lib/db.ts' <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// tables: users(id uuid pk, email text unique, password_hash text), sessions(token_hash text pk, user_id uuid, expires_at timestamptz)
J
cat > 'lib/session.ts' <<'J'
import { createHash, randomBytes } from "node:crypto";
import { pool } from "@/lib/db";
export const SESSION_DAYS = 30;
/** Returns the raw session token; only its hash is stored. */
export async function createSession(userId: string): Promise<string> {
  const token = randomBytes(32).toString("base64url");
  const hash = createHash("sha256").update(token).digest("hex");
  await pool.query("insert into sessions (token_hash, user_id, expires_at) values ($1, $2, now() + interval '30 days')", [hash, userId]);
  return token;
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
