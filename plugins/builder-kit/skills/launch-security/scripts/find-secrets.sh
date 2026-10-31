#!/usr/bin/env bash
# Grep a repo or build folder for likely secrets (checks 02, 11, 24). Values are masked to 4 chars.
# Usage: find-secrets.sh [dir]   (default: .)   e.g. find-secrets.sh .next/static
# Exit code 1 if anything matched. Not a substitute for gitleaks/trufflehog on Git history.
set -u

dir="${1:-.}"
pattern='(sk_live_|sk_test_|rk_live_|sk-ant-|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|github_pat_|xox[bpas]-|AIza[0-9A-Za-z_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|service_role|(postgres|postgresql|mysql|mongodb(\+srv)?)://[^:/ ]+:[^@ ]+@|(api[_-]?key|secret|password|token)["'\'' ]*[:=]["'\'' ]*[A-Za-z0-9/+_-]{16,})'

matches=$(grep -rIniE "$pattern" "$dir" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv \
  --exclude='*.lock' --exclude='package-lock.json' --exclude='pnpm-lock.yaml' 2>/dev/null)

if [ -z "$matches" ]; then
  echo "OK: no secret patterns found in $dir"
  exit 0
fi

# Mask: keep file:line and the first 4 chars of each matched token.
printf '%s\n' "$matches" | while IFS= read -r line; do
  loc="${line%%:*}"; rest="${line#*:}"; ln="${rest%%:*}"; text="${rest#*:}"
  hit=$(printf '%s' "$text" | grep -oiE "$pattern" | head -1)
  printf '%s:%s: %s****\n' "$loc" "$ln" "${hit:0:4}"
done
echo "FAIL: review each hit. Secrets in client code or history must be moved server-side AND rotated (check 25)."
exit 1
