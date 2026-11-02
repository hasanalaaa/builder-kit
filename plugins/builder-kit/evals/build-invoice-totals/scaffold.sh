#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'lib' 'migrations'
cat > 'package.json' <<'J'
{ "name": "billing", "private": true, "dependencies": { "next": "16.0.0", "pg": "8.13.0" } }
J
cat > 'lib/db.ts' <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
J
cat > 'migrations/001_init.sql' <<'J'
create table customers (
  id uuid primary key default gen_random_uuid(),
  name text not null
);
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
