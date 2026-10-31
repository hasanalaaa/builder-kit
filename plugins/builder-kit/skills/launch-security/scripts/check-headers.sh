#!/usr/bin/env bash
# Check a live URL for HTTPS redirect, security headers, cookie flags and CORS reflection (checks 04, 13, 14, 15, 20).
# Usage: check-headers.sh https://yourapp.com [api-path-for-cors]   e.g. check-headers.sh https://yourapp.com /api/me
# Run only against domains you own. Exit code 1 if any check fails.
set -u

url="${1:?usage: check-headers.sh https://yourapp.com [api-path]}"
url="${url%/}"
api="${2:-/}"
fail=0
ok()  { printf 'PASS  %s\n' "$1"; }
bad() { printf '\033[31mFAIL  %s\033[0m\n' "$1"; fail=1; }

headers=$(curl -s -I -L -m 15 "$url" | tr -d '\r')
lc=$(printf '%s' "$headers" | tr 'A-Z' 'a-z')
has() { printf '%s' "$lc" | grep -q "^$1:"; }

# 04: plain HTTP must redirect to HTTPS
http_url="http://${url#*://}"
loc=$(curl -s -o /dev/null -m 15 -w '%{http_code} %{redirect_url}' "$http_url")
case "$loc" in 30[1278]\ https://*) ok "HTTP redirects to HTTPS ($loc)";; *) bad "HTTP does not redirect to HTTPS (got: $loc)";; esac

# 14: required headers
for h in strict-transport-security content-security-policy x-content-type-options referrer-policy permissions-policy; do
  has "$h" && ok "$h present" || bad "$h missing"
done
if has x-frame-options || printf '%s' "$lc" | grep -q "frame-ancestors"; then ok "clickjacking protection present"; else bad "no X-Frame-Options or CSP frame-ancestors"; fi
printf '%s' "$lc" | grep -q "^content-security-policy:.*'unsafe-eval'" && bad "CSP allows 'unsafe-eval'"
printf '%s' "$lc" | grep -q "^content-security-policy-report-only:" && ! has content-security-policy && bad "CSP is report-only, not enforced"

# 20: version-leaking headers
has x-powered-by && bad "X-Powered-By present: $(printf '%s' "$headers" | grep -i '^x-powered-by:')"
printf '%s' "$headers" | grep -iE '^server: .*[0-9]+\.[0-9]+' >/dev/null && bad "Server header leaks a version"

# 15: cookie flags (only cookies set on this response)
printf '%s\n' "$headers" | grep -i '^set-cookie:' | while IFS= read -r c; do
  name=$(printf '%s' "$c" | sed -E 's/^[Ss]et-[Cc]ookie: *([^=]+)=.*/\1/')
  l=$(printf '%s' "$c" | tr 'A-Z' 'a-z')
  miss=""
  printf '%s' "$l" | grep -q '; *secure' || miss="$miss Secure"
  printf '%s' "$l" | grep -q '; *httponly' || miss="$miss HttpOnly"
  printf '%s' "$l" | grep -q '; *samesite=' || miss="$miss SameSite"
  [ -z "$miss" ] && echo "PASS  cookie $name flags" || echo "WARN  cookie $name missing:$miss (required for auth/session cookies)"
done

# 13: CORS must not reflect an unknown origin
cors=$(curl -s -I -m 15 -H "Origin: https://evil.example" "$url$api" | tr -d '\r' | tr 'A-Z' 'a-z')
acao=$(printf '%s' "$cors" | grep '^access-control-allow-origin:' | sed 's/^[^:]*: *//')
acac=$(printf '%s' "$cors" | grep -c '^access-control-allow-credentials: *true')
if [ "$acao" = "https://evil.example" ]; then bad "CORS reflects arbitrary origin on $api"
elif [ "$acao" = "*" ] && [ "$acac" -gt 0 ]; then bad "CORS wildcard with credentials on $api"
else ok "CORS does not trust unknown origin on $api"; fi

[ "$fail" -eq 0 ] && echo "RESULT: all checks passed" || echo "RESULT: failures found"
exit "$fail"
