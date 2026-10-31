#!/usr/bin/env bash
# Probe YOUR OWN domain for sensitive files that must never be public (check 23).
# Usage: check-exposed.sh https://yourapp.com [extra/path ...]
# Exit code 1 if any path returns 200.
set -u

base="${1:?usage: check-exposed.sh https://yourapp.com [extra/path ...]}"
base="${base%/}"
shift

paths=(
  .env .env.local .env.production .env.development .env.backup .env.bak .env.old
  .git/config .git/HEAD .gitignore .DS_Store .vscode/settings.json .idea/workspace.xml
  backup.zip backup.tar.gz db.sql dump.sql database.sql database.sqlite data.db
  config.json config.yml docker-compose.yml .npmrc phpinfo.php server-status
  swagger.json openapi.json graphql
  "$@"
)

exposed=0
for p in "${paths[@]}"; do
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "$base/${p#/}")
  if [ "$code" = "200" ]; then
    printf '\033[31m%s  /%s  <-- EXPOSED\033[0m\n' "$code" "${p#/}"
    exposed=1
  else
    printf '%s  /%s\n' "$code" "${p#/}"
  fi
done

# ponytail: .map files are not auto-discovered; pass them as extra paths (e.g. _next/static/chunks/main.js.map).
[ "$exposed" -eq 0 ] && echo "OK: nothing returned 200." || echo "FAIL: block the paths marked EXPOSED, then rotate any secret they held (check 25)."
exit "$exposed"
