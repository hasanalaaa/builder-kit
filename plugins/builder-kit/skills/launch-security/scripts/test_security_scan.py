#!/usr/bin/env python3
# security-scan: ignore-file  (fixtures contain the patterns under test)
"""Tests for security_scan.py: a messy tree must trigger every rule, a clean tree must stay silent.

Run: python3 test_security_scan.py
"""
import argparse  # noqa: F401  (used by some fixtures)
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from security_scan import findings, run  # noqa: E402


def main():
    bad = {
        "src/a.ts": "const key = 'sk_live_" + "abcdefghijklmnop';\nconst q = `SELECT * FROM users WHERE id = ${id}`;\n"
                    "el.innerHTML = input;\nconst t = Math.random().toString(36); // reset token\n"
                    "const s = process.env.JWT_SECRET || 'dev';\nres.redirect(req.query.next);\n"
                    "localStorage.setItem('auth_token', t);\nexec(`convert ${file}`);\n"
                    "await db.user.update({ data: req.body });\n",
        "src/c.tsx": "'use client';\nconst k = process.env.STRIPE_SECRET_KEY;\n",
        "src/env.ts": "const x = process.env.NEXT_PUBLIC_STRIPE_SECRET;\n",
        "api/b.py": "cur.execute(f\"SELECT * FROM t WHERE id = {uid}\")\nrequests.get(u, verify=False)\n"
                    "app.run(debug=True)\nhashlib.md5(password.encode())\npickle.loads(blob)\n",
        "app/api/webhooks/stripe/route.ts": "export async function POST(req) { await fulfil(await req.json()); }\n",
        "firestore.rules": "match /{d=**} { allow read, write: if true; }\n",
        "supabase/migrations/1.sql": "create table public.orders (id uuid);\ncreate table public.notes (id uuid);\n"
                                     "alter table public.notes enable row level security;\n",
        "server.js": "app.use(cors({ origin: true, credentials: true }));\n",
        "app/api/preview/route.ts": "if (isPrivateIp(addr)) throw new Error('blocked');\nconst r = await fetch(url, { signal });\n",
    }
    good = {
        "src/a.ts": "const rows = await sql`SELECT * FROM users WHERE id = ${id}`;\nconst t = randomBytes(32).toString('base64url');\n"
                    "el.textContent = input;\nconst s = env.JWT_SECRET;\nredirect(safeNext(params.get('next')));\n",
        "api/b.py": "cur.execute(\"SELECT * FROM t WHERE id = %s\", (uid,))\nsecrets.token_urlsafe(32)\n",
        "app/api/webhooks/stripe/route.ts": "const e = stripe.webhooks.constructEvent(body, sig, secret);\n",
        "supabase/migrations/1.sql": "create table public.orders (id uuid);\nalter table public.orders enable row level security;\n",
        "server.js": "app.use(cors({ origin: ['https://app.example.com'], credentials: true }));\n",
        "app/api/preview/route.ts": "if (isPrivateIp(addr)) throw new Error('blocked');\nconst r = await fetch(url, { redirect: 'manual' });\n",
    }
    expect = {"hardcoded-secret", "sql-string-built", "xss-sink", "weak-random-secret", "secret-fallback", "open-redirect",
              "token-in-localstorage", "command-injection", "mass-assignment", "server-secret-in-client",
              "secret-in-public-env", "tls-verification-off", "debug-in-prod", "weak-password-hash", "unsafe-deserialize",
              "webhook-unsigned", "ssrf-follows-redirects", "firebase-open-rules", "table-without-rls", "cors-any-origin-with-credentials"}
    for name, tree in (("bad", bad), ("good", good)):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in tree.items():
                path = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)
            run(tmp)
            rules = {f[2] for f in findings}
            if name == "bad":
                missing = expect - rules
                assert not missing, f"selftest missed: {sorted(missing)}"
                assert ("table-without-rls", "orders") in {(f[2], f[5].split("'")[1]) for f in findings if f[2] == "table-without-rls"}
            else:
                assert not findings, f"clean tree should be clean, got {findings}"
    print("selftest OK")


if __name__ == "__main__":
    main()
