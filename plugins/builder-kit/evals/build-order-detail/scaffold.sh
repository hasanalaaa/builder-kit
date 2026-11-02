#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'app/api/orders' 'lib'
cat > 'package.json' <<'J'
{ "name": "shop", "private": true, "dependencies": { "next": "16.0.0", "pg": "8.13.0", "zod": "4.1.0" } }
J
cat > 'lib/db.ts' <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// tables: orders(id uuid pk, user_id uuid not null, status text, shipping_address text, note text, total_cents int)
J
cat > 'lib/auth.ts' <<'J'
import { cookies } from "next/headers";
import { pool } from "@/lib/db";
export async function getCurrentUser(): Promise<{ id: string; email: string } | null> {
  const token = (await cookies()).get("session")?.value;
  if (!token) return null;
  const { rows } = await pool.query(
    "select u.id, u.email from sessions s join users u on u.id = s.user_id where s.token_hash = encode(sha256($1::bytea), 'hex') and s.expires_at > now()",
    [token],
  );
  return rows[0] ?? null;
}
J
cat > 'app/api/orders/route.ts' <<'J'
import { pool } from "@/lib/db";
import { getCurrentUser } from "@/lib/auth";
export async function GET() {
  const user = await getCurrentUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });
  const { rows } = await pool.query("select id, status, total_cents from orders where user_id = $1 order by id desc", [user.id]);
  return Response.json(rows);
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
