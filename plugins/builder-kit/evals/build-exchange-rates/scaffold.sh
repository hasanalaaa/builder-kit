#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'lib'
cat > 'package.json' <<'J'
{ "name": "checkout", "private": true, "dependencies": { "next": "16.0.0" } }
J
cat > 'lib/logger.ts' <<'J'
export const logger = {
  info: (msg: string, data?: Record<string, unknown>) => console.log(JSON.stringify({ level: "info", msg, ...data })),
  error: (msg: string, data?: Record<string, unknown>) => console.error(JSON.stringify({ level: "error", msg, ...data })),
};
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
