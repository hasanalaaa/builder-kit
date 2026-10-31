#!/usr/bin/env python3
# security-scan: ignore-file  (this file contains the very patterns it searches for)
"""Static scan for the security mistakes AI-built apps make most (stdlib only).

Every finding names its launch-security check. A match is a lead, not proof:
read the code, fix the root cause, and report false positives instead of hiding them.

Usage:  security_scan.py [ROOT]
Exit code 1 when any ERROR is found. Tests: python3 test_security_scan.py
To silence one reviewed line, add a comment containing  security-scan: ignore  and the reason.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

JS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte")
PY = (".py",)
SRC = JS + PY + (".go", ".rb", ".php", ".java", ".kt", ".swift", ".dart", ".cs", ".rs")
CONF = (".json", ".yaml", ".yml", ".toml", ".xml", ".plist", ".gradle", ".properties")
TPL = (".html", ".jinja", ".j2", ".njk", ".hbs", ".ejs")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".output", "coverage",
               "vendor", ".venv", "venv", "__pycache__", "Pods", ".expo", "DerivedData", "target", ".turbo", ".cache",
               "third_party", "third-party", "managed_components", ".dart_tool", ".gradle"}
LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "composer.lock", "Podfile.lock", "Cargo.lock"}

SQL = r"(?i:\bselect\b[^`'\"]*\bfrom\b|\binsert\s+into\b|\bupdate\b[^`'\"]*\bset\b|\bdelete\s+from\b)"
SECRET_WORD = r"\w*(?:SECRET|PRIVATE|PASSWORD|SERVICE_ROLE|TOKEN|API_KEY)\w*"

# (level, check, rule, extensions, regex, message)
RULES = [
    ("ERROR", "02", "hardcoded-secret", SRC + CONF,
     r"sk_live_[0-9A-Za-z]{8,}|rk_live_[0-9A-Za-z]{8,}|sk-ant-[\w-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{32,}|AKIA[0-9A-Z]{16}|"
     r"ghp_[A-Za-z0-9]{30,}|github_pat_\w{20,}|xox[bpa]-[0-9A-Za-z-]{10,}|AIza[0-9A-Za-z_-]{35}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
     r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^:/\s'\"]+:[^@\s'\"]{3,}@",
     "hard-coded credential; move it to a server-only env var and rotate it (25)"),
    ("ERROR", "02", "secret-in-public-env", SRC + (".env",),
     r"\b(?:NEXT_PUBLIC_|VITE_|REACT_APP_|EXPO_PUBLIC_|NUXT_PUBLIC_)\w*(?:SECRET|PRIVATE|PASSWORD|SERVICE_ROLE)\w*",
     "secret behind a public prefix is shipped to every browser; make it server-only and rotate it"),
    ("ERROR", "11", "secret-fallback", SRC,
     rf"(?:process\.env|import\.meta\.env)\.{SECRET_WORD}\s*(?:\|\||\?\?)\s*['\"`][^'\"`]|"
     rf"os\.(?:getenv|environ\.get)\(\s*['\"]{SECRET_WORD}['\"]\s*,\s*['\"][^'\"]",
     "insecure default for a secret; fail at startup instead (secure-patterns P1)"),
    ("ERROR", "01", "jwt-hardcoded-key", SRC,
     r"jwt\.(?:sign|encode)\([^)]*,\s*['\"][^'\"]{1,64}['\"]",
     "JWT signed with a hard-coded key; load a 32+ byte secret from env"),
    ("WARN", "01", "jwt-decode-unverified", JS, r"\bjwt\.decode\(",
     "jsonwebtoken decode() does not verify the signature; use jwt.verify() with an algorithm allowlist"),
    ("ERROR", "01", "jwt-verify-disabled", PY,
     r"verify_signature['\"]?\s*:\s*False|algorithms\s*=\s*\[[^\]]*['\"]none['\"]",
     "JWT signature verification disabled"),
    ("ERROR", "04", "tls-verification-off", SRC,
     r"\bverify\s*=\s*False|rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED|InsecureSkipVerify\s*:\s*true",
     "TLS certificate verification disabled"),
    ("WARN", "04", "plain-http-url", SRC,
     # Local/LAN hosts and URL templates are excluded: devices on the user's own network often have no TLS.
     r"['\"`]http://(?!localhost|127\.|0\.0\.0\.0|\[::1\]|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|169\.254\.|"
     r"[\w.-]+\.local\b|host\b(?!\.)|www\.w3\.org|schemas\.|xmlns|example\.|\$|\{|['\"`])",
     "plain-HTTP URL; use https://"),
    ("WARN", "07", "xss-sink", JS + TPL + PY,
     r"dangerouslySetInnerHTML|v-html=|\{@html\s|\.innerHTML\s*=|\.outerHTML\s*=|insertAdjacentHTML\(|document\.write\(|"
     r"bypassSecurityTrust\w+\(|\|\s*safe\b|mark_safe\(|Markup\(",
     "raw HTML sink; render as text or sanitize with DOMPurify / a strict allowlist sanitizer"),
    ("ERROR", "07", "code-eval", JS + PY, r"(?<![\w.$])eval\(|\bnew Function\(",
     "dynamic code execution"),
    ("ERROR", "10", "sql-string-built", JS,
     rf"(?<![\w$.])`(?=[^`]*{SQL})[^`]*\$\{{|{SQL}[^'\"\n]*['\"]\s*\+\s*[\w(]",
     "SQL built from a string; use parameters or a tagged template (sql`…`, $queryRaw`…`)"),
    ("ERROR", "10", "sql-string-built", PY,
     rf"\bf['\"](?=[^'\"]*{SQL})[^'\"]*\{{|{SQL}[^'\"\n]*['\"]\s*(?:%\s*[\w(]|\.format\()",
     "SQL built from a string; pass parameters to execute()"),
    ("WARN", "10", "orm-raw-unsafe", JS + PY,
     r"\$(?:query|execute)RawUnsafe\(|sequelize\.literal\(|\bsql\.raw\(|\.raw\(\s*`[^`]*\$\{|\.extra\(",
     "raw/unsafe ORM call; make sure no user input reaches it unparameterized"),
    ("ERROR", "10", "command-injection", JS,
     r"\bexec(?:Sync)?\(\s*`[^`]*\$\{|\bexec(?:Sync)?\([^)]*['\"]\s*\+",
     "shell command built from a string; use execFile/spawn with an argument array"),
    ("ERROR", "10", "command-injection", PY,
     r"subprocess\.\w+\(\s*f['\"]|os\.system\(\s*f['\"]",
     "shell command built from an f-string; pass an argument list without shell=True"),
    ("WARN", "10", "shell-true", PY, r"shell\s*=\s*True|os\.system\(",
     "shell execution; never with user input"),
    ("WARN", "H8", "unsafe-deserialize", PY + (".php",),
     r"pickle\.loads?\(|yaml\.load\((?![^)]*SafeLoader)|marshal\.loads\(|\bunserialize\(",
     "unsafe deserialization; use JSON or yaml.safe_load"),
    ("WARN", "05", "weak-password-hash", SRC,
     r"(?i)(?=.*passw)(?=.*(?:\bmd5\b|\bsha1\b|\bsha256\b|createHash\(|hashlib\.))",
     "fast hash near a password; passwords need Argon2id/bcrypt (hashing reset tokens with SHA-256 is fine)"),
    ("WARN", "17", "weak-random-secret", SRC,
     r"(?i)(?=.*(?:token|secret|otp|nonce|reset|session|api.?key|salt|password))"
     r"(?=.*(?:Math\.random\(|\brandom\.(?:random|randint|choice|choices|getrandbits)\())",
     "non-cryptographic randomness for a secret; use crypto.randomBytes / secrets.token_urlsafe"),
    ("ERROR", "13", "cors-reflects-origin", SRC,
     r"Access-Control-Allow-Origin['\"]?\s*,\s*(?:req\.headers\.origin|origin|request\.headers)",
     "CORS reflects any origin; use an exact allowlist"),
    ("WARN", "13", "cors-wildcard", SRC,
     r"Access-Control-Allow-Origin['\"]?\s*[,:]\s*['\"]\*|allow_origins\s*=\s*\[\s*['\"]\*['\"]|\borigin\s*:\s*(?:['\"]\*['\"]|true)\b",
     "CORS allows any origin; fine only for public, cookie-less, non-personal endpoints"),
    ("ERROR", "20", "debug-in-prod", PY, r"\.run\([^)]*debug\s*=\s*True",
     "debug server enabled (the Werkzeug debugger allows remote code execution)"),
    ("WARN", "20", "debug-setting", PY, r"^\s*DEBUG\s*=\s*True",
     "DEBUG=True; must be off in production via env config"),
    ("WARN", "20", "error-detail-leak", JS,
     r"(?:res\.(?:json|send)|Response\.json|NextResponse\.json)\([^)]*\b(?:err|error|e)\.(?:stack|message)",
     "internal error details returned to the client; return a generic message + request ID"),
    ("ERROR", "03", "firebase-open-rules", (".rules",), r"allow\s+[\w, ]+:\s*if\s+true",
     "Firebase rule allows everyone"),
    ("WARN", "03", "firebase-test-mode", (".rules",), r"request\.time\s*<\s*timestamp\.date",
     "Firebase test-mode rule"),
    ("WARN", "09", "role-from-user-metadata", SRC + (".sql",),
     r"(?i)user_metadata(?=.*(?:role|admin|plan|tier))|(?i:(?:role|admin|plan|tier).*)user_metadata",
     "user_metadata is editable by the user; read roles from app_metadata or a table"),
    ("WARN", "15", "token-in-localstorage", JS,
     r"(?i)localStorage\.setItem\(\s*['\"`][^'\"`]*(?:token|jwt|session|auth)",
     "auth token in localStorage is readable by any XSS; prefer HttpOnly cookies"),
    ("WARN", "15", "insecure-cookie-flag", SRC,
     r"(?i)(?=.*cookie)(?=.*(?:httponly|secure)\s*[:=]\s*false)",
     "cookie flag disabled; auth cookies need HttpOnly + Secure + SameSite"),
    ("ERROR", "01", "open-redirect", SRC,
     r"\bredirect\(\s*(?:req\.(?:query|body|params)|request\.(?:args|GET|POST|query_params)|searchParams\.get\()",
     "redirect target taken from the request; allow only same-site paths (secure-patterns P8)"),
    ("WARN", "B2", "ssrf-candidate", SRC,
     r"\b(?:fetch|axios(?:\.\w+)?|got|requests\.\w+|httpx\.\w+|urlopen)\(\s*(?:req\.(?:body|query|params)|"
     r"request\.(?:args|json|form|query_params)|searchParams\.get\()",
     "server fetches a user-supplied URL; apply the SSRF guard (secure-patterns P14)"),
    ("WARN", "06", "mass-assignment", JS,
     r"\.(?:create|update|insert|upsert|updateOne|insertOne)\(\s*\{?\s*(?:data\s*:\s*)?(?:\.\.\.)?(?:req\.body|await req\.json\(\)|body)\s*[,})]",
     "request body written straight to the database; copy allowed fields from a strict schema"),
]
COMPILED = [(lvl, chk, rule, exts, re.compile(rx), msg) for lvl, chk, rule, exts, rx, msg in RULES]

findings = []


def report(level, check, rule, path, line, msg):
    findings.append((level, check, rule, path, line, msg))


def wanted(rel):
    parts = rel.split(os.sep)
    name = parts[-1]
    if any(p in IGNORE_DIRS for p in parts[:-1]) or name in LOCKFILES or name.endswith((".min.js", ".map")):
        return False
    return name.startswith(".env") or name.endswith(SRC + CONF + TPL + (".rules", ".sql"))


def list_files(root):
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "-co", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout
        return sorted(f for f in (os.path.normpath(x) for x in out.splitlines() if x) if wanted(f)), True
    except (OSError, subprocess.CalledProcessError):
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            files += [os.path.relpath(os.path.join(dirpath, f), root) for f in filenames]
        return sorted(f for f in files if wanted(f)), False


def is_test(rel):
    return bool(re.search(bk.TEST_CODE, rel.replace(os.sep, "/")))


def ext_of(rel):
    name = os.path.basename(rel)
    return ".env" if name.startswith(".env") else os.path.splitext(name)[1]


def scan_file(rel, text):
    if "security-scan: ignore-file" in text[:500]:
        return
    ext = ext_of(rel)
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if "security-scan: ignore" in line or len(line) > 2000:
            continue
        for lvl, chk, rule, exts, rx, msg in COMPILED:
            if rule == "plain-http-url" and is_test(rel):
                continue  # test fixtures legitimately use http URLs
            if ext in exts and rx.search(line):
                report("WARN" if is_test(rel) else lvl, chk, rule, rel, i, msg)
    # File-level rules
    if ext in JS and re.search(r"^['\"]use client['\"]", text, re.M):
        for i, line in enumerate(lines, 1):
            if re.search(r"process\.env\.(?!NEXT_PUBLIC_)\w+|service_role", line) and "security-scan: ignore" not in line:
                report("ERROR", "02", "server-secret-in-client", rel, i, "client component references a server-only secret")
    if ext in SRC and "webhook" in rel.lower() and not is_test(rel) and not re.search(
            r"constructEvent|verif\w*|signature|hmac|svix|timingSafeEqual|compare_digest", text, re.I):
        report("WARN", "19", "webhook-unsigned", rel, 0, "webhook handler without visible signature verification")
    if re.search(r"credentials\s*:\s*true|allow_credentials\s*=\s*True", text) and re.search(
            r"\borigin\s*:\s*(?:['\"]\*['\"]|true)\b|allow_origins\s*=\s*\[\s*['\"]\*['\"]", text):
        report("ERROR", "13", "cors-any-origin-with-credentials", rel, 0, "any origin allowed together with credentials")


CREATE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?(?:\"?public\"?\.)?\"?(\w+)\"?\s*\(", re.I)
RLS = re.compile(r"alter\s+table\s+(?:only\s+)?(?:if\s+exists\s+)?(?:\"?public\"?\.)?\"?(\w+)\"?\s+enable\s+row\s+level\s+security", re.I)


def scan_repo(root, files, contents, in_git):
    created, protected = {}, set()
    for rel in files:
        if rel.endswith(".sql"):
            for m in CREATE.finditer(contents[rel]):
                created.setdefault(m.group(1).lower(), rel)
            protected |= {m.group(1).lower() for m in RLS.finditer(contents[rel])}
    supabase = os.path.isdir(os.path.join(root, "supabase")) or any("auth.uid()" in contents[f] for f in files if f.endswith(".sql"))
    for table, rel in sorted(created.items()):
        if table not in protected:
            report("ERROR" if supabase else "WARN", "03", "table-without-rls", rel, 0,
                   f"table '{table}' never gets 'enable row level security' (secure-patterns P5)")
    if in_git:
        for rel in files:
            name = os.path.basename(rel)
            if name.startswith(".env") and not re.search(r"example|sample|template|dist", name, re.I):
                report("ERROR", "24", "env-file-committed", rel, 0, "env file tracked by Git; untrack it, scan history (24) and rotate (25)")


def run(root):
    findings.clear()
    files, in_git = list_files(root)
    contents = {}
    for rel in files:
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
                contents[rel] = fh.read()
        except OSError:
            contents[rel] = ""
        scan_file(rel, contents[rel])
    scan_repo(root, files, contents, in_git)
    return files


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    args = p.parse_args()
    root = os.path.abspath(args.root)
    files = run(root)
    return bk.report(findings, "security_scan", root, note=f" ({len(files)} files)")


if __name__ == "__main__":
    sys.exit(main())
