#!/usr/bin/env python3
"""Self-test for context_pack. Run: python3 test_context_pack.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import context_pack  # noqa: E402

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        files = {
            "package.json": '{"scripts": {"dev": "next dev", "test": "vitest", "lint": "eslint .", "build": "next build"},'
                            ' "dependencies": {"next": "15.0.0", "@supabase/supabase-js": "2"}, "devDependencies": {"typescript": "5", "vitest": "2"}}',
            "pnpm-lock.yaml": "",
            ".env.example": "DATABASE_URL=\nSTRIPE_SECRET_KEY=\n",
            "app/layout.tsx": "",
            "supabase/migrations/001.sql": "",
            "SPEC.md": "",
        }
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
            with open(os.path.join(d, rel), "w") as f:
                f.write(body)
        out = context_pack.render(d, context_pack.detect(d))
        for needle in ("Next.js 15.0.0", "Supabase", "TypeScript", "pnpm install", "test: pnpm test", "build: pnpm build",
                       "DATABASE_URL", "STRIPE_SECRET_KEY", "app/layout.tsx", "Supabase schema", "SPEC.md"):
            assert needle in out, (needle, out)
    print("selftest OK")
