#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'lib'
cat > 'package.json' <<'J'
{ "name": "storefront", "private": true, "dependencies": { "next": "16.0.0", "pg": "8.13.0", "zod": "4.1.0" } }
J
cat > 'lib/db.ts' <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// products(id uuid pk, name text, category text, price_cents int, created_at timestamptz) -- ~200k rows
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
