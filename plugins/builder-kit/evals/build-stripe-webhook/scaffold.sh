#!/usr/bin/env bash
set -euo pipefail
mkdir -p lib app/api/credits
cat > package.json <<'J'
{ "name": "credits-app", "private": true, "dependencies": { "next": "16.0.0", "stripe": "19.0.0", "pg": "8.13.0", "zod": "4.1.0" } }
J
cat > lib/db.ts <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// tables: users(id uuid pk, credits int not null default 0)
J
cat > app/api/credits/route.ts <<'J'
import { pool } from "@/lib/db";
export async function GET(req: Request) {
  const userId = req.headers.get("x-user-id");
  const { rows } = await pool.query("select credits from users where id = $1", [userId]);
  return Response.json({ credits: rows[0]?.credits ?? 0 });
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
