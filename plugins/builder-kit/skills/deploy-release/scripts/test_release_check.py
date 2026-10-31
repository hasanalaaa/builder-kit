#!/usr/bin/env python3
"""Self-test for release_check. Run: python3 test_release_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_check  # noqa: E402

BAD = {
    "package.json": '{"name": "x", "scripts": {}}',
    "app/api/users/route.ts": "const k = process.env.STRIPE_SECRET_KEY\nconst u = process.env.DATABASE_URL\n",
    "supabase/migrations/001.sql": "create table t(id int primary key);\n",
    "Dockerfile": "FROM node:latest\nENV API_KEY=abc123\nCOPY . .\nCMD node server.js\n",
}
GOOD = {
    "package.json": '{"name": "x", "engines": {"node": ">=22"}, "scripts": {"build": "next build", "db:migrate": "supabase migration up"}}',
    "pnpm-lock.yaml": "lockfileVersion: 9\n",
    ".env.example": "STRIPE_SECRET_KEY=\nDATABASE_URL=\n",
    "app/api/users/route.ts": "const k = process.env.STRIPE_SECRET_KEY\nconst u = process.env.DATABASE_URL\n",
    "app/api/health/route.ts": "export const GET = () => Response.json({ ok: true })\n",
    "supabase/migrations/001.sql": "create table t(id int primary key);\n",
    ".github/workflows/ci.yml": ("permissions: { contents: read }\njobs:\n  c:\n    steps:\n"
                                "      - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567\n"
                                "      - run: pnpm lint && pnpm typecheck && pnpm test && pnpm build && pnpm db:migrate\n"),
    "Dockerfile": "FROM node:22.11-alpine AS run\nUSER node\nHEALTHCHECK CMD wget -qO- localhost:3000/api/health\nCMD node server.js\n",
    ".dockerignore": ".git\n.env*\nnode_modules\n",
}


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in release_check.run(d)}


if __name__ == "__main__":
    got = run_on(BAD)
    want = {"no-ci", "no-env-example", "no-lockfile", "node-unpinned", "no-build-script", "docker-unpinned-base",
            "docker-root", "docker-no-healthcheck", "docker-secret", "no-dockerignore", "no-health-endpoint", "migrations-manual"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD)
    assert not got, sorted(got)
    print("selftest OK")
