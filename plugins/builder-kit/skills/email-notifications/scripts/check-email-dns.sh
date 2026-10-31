#!/usr/bin/env bash
# check-email-dns.sh: check a sending domain's email authentication records.
# Usage: check-email-dns.sh example.com [dkim-selector ...]
# Checks MX, SPF (count + lookups estimate), DMARC policy, DKIM on common or given selectors, BIMI, MTA-STS.
# Exit 1 when SPF or DMARC is missing or SPF is duplicated.
set -u
domain="${1:-}"
if [ -z "$domain" ]; then
  echo "usage: $0 domain [dkim-selector ...]" >&2
  exit 2
fi
shift
if ! command -v dig >/dev/null 2>&1; then
  echo "dig not found (install bind/dnsutils)" >&2
  exit 2
fi
fail=0
txt() { dig +short TXT "$1" 2>/dev/null | sed 's/" "//g' | tr -d '"'; }
ok() { printf 'PASS  %s\n' "$1"; }
warn() { printf 'WARN  %s\n' "$1"; }
bad() { printf 'FAIL  %s\n' "$1"; fail=1; }

echo "Email DNS for $domain"
mx=$(dig +short MX "$domain" 2>/dev/null)
if [ -n "$mx" ]; then ok "MX: $(echo "$mx" | tr '\n' ' ')"; else warn "No MX: replies and DMARC reports to this domain won't arrive"; fi

spf=$(txt "$domain" | grep -i '^v=spf1' || true)
spf_count=$(printf '%s\n' "$spf" | grep -c 'v=spf1' || true)
if [ -z "$spf" ]; then
  bad "No SPF record (TXT v=spf1 ...)"
elif [ "$spf_count" -gt 1 ]; then
  bad "Multiple SPF records ($spf_count): merge into one"
else
  lookups=$(printf '%s' "$spf" | grep -oiE '(include:|a:|mx:|ptr:|exists:|redirect=|(^| )a( |$)|(^| )mx( |$))' | wc -l | tr -d ' ')
  ok "SPF: $spf"
  [ "$lookups" -gt 10 ] && bad "SPF has ~$lookups DNS lookups (limit 10)"
  printf '%s' "$spf" | grep -qE '[-~]all' || warn "SPF does not end with -all or ~all"
  printf '%s' "$spf" | grep -q '+all' && bad "SPF uses +all (anyone can send as you)"
fi

dmarc=$(txt "_dmarc.$domain" | grep -i '^v=DMARC1' || true)
if [ -z "$dmarc" ]; then
  bad "No DMARC record at _dmarc.$domain"
else
  ok "DMARC: $dmarc"
  policy=$(printf '%s' "$dmarc" | grep -oiE 'p=[a-z]+' | head -1 | cut -d= -f2)
  case "$policy" in
    reject) ok "DMARC policy reject (enforced)";;
    quarantine) ok "DMARC policy quarantine";;
    none) warn "DMARC p=none: monitoring only; move to quarantine/reject after reviewing reports";;
    *) warn "DMARC policy unclear";;
  esac
  printf '%s' "$dmarc" | grep -q 'rua=' || warn "DMARC has no rua= reporting address"
fi

selectors="$*"
[ -z "$selectors" ] && selectors="default google selector1 selector2 resend s1 s2 k1 k2 mail dkim smtp pm postmark mandrill amazonses mxvault"
found=""
for s in $selectors; do
  rec=$(dig +short TXT "$s._domainkey.$domain" 2>/dev/null; dig +short CNAME "$s._domainkey.$domain" 2>/dev/null)
  [ -n "$rec" ] && found="$found $s"
done
if [ -n "$found" ]; then ok "DKIM selectors found:$found"; else warn "No DKIM found on common selectors (pass your provider's selector as an argument)"; fi

bimi=$(txt "default._bimi.$domain" | grep -i '^v=BIMI1' || true)
[ -n "$bimi" ] && ok "BIMI: $bimi" || printf 'INFO  No BIMI record (optional)\n'
sts=$(txt "_mta-sts.$domain" | grep -i '^v=STSv1' || true)
[ -n "$sts" ] && ok "MTA-STS: $sts" || printf 'INFO  No MTA-STS (optional inbound hardening)\n'

[ "$fail" -eq 0 ] && echo "Result: no failures" || echo "Result: failures found"
exit "$fail"
