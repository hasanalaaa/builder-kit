#!/usr/bin/env python3
"""Self-test for docs_check. Run: python3 test_docs_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docs_check  # noqa: E402

GOOD_README = """# Rawdah
Daily nursery updates for parents, in Arabic and English. This README explains setup, running, testing and deploying.

## Quick start
1. `pnpm install`
2. `cp .env.example .env.local` and fill the environment variables
3. `pnpm dev`

## Test
`pnpm test` and `pnpm run e2e`

## Deploy
Push to main; CI deploys to production. Rollback: docs/runbooks/rollback.md
"""


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in docs_check.run(d)}


if __name__ == "__main__":
    bad = {
        "package.json": '{"scripts": {"dev": "next dev"}}',
        "docs/setup.md": "Run `pnpm run seed` then `npm run e2e`.\n",
        "src/db.ts": "const u = process.env.DATABASE_URL\n",
    }
    got = run_on(bad)
    want = {"no-readme", "no-agent-context", "no-changelog", "no-runbooks", "doc-command-missing", "no-env-example"}
    assert want <= got, sorted(want - got)
    good = {
        "README.md": GOOD_README,
        "CLAUDE.md": "# Project facts\n",
        "CHANGELOG.md": "# Changelog\n",
        "docs/runbooks/rollback.md": "# Rollback\n",
        "package.json": '{"scripts": {"dev": "next dev", "test": "vitest", "e2e": "playwright test"}}',
        ".env.example": "DATABASE_URL=\n",
        "src/db.ts": "const u = process.env.DATABASE_URL\n",
    }
    got = run_on(good)
    assert not got, sorted(got)
    print("selftest OK")
