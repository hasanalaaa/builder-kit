#!/usr/bin/env python3
"""Self-test for obs_check. Run: python3 test_obs_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_check  # noqa: E402

BAD = {
    "package.json": '{"dependencies": {"next": "x", "expo": "x"}}',
    "app/api/login/route.ts": "export async function POST(req){ const b = await req.json(); console.log('login', b.password); console.log(b) }\n",
    "app/layout.tsx": "<script src=\"https://www.googletagmanager.com/gtag/js\"></script>\n",
}
GOOD = {
    "package.json": '{"dependencies": {"next": "x", "@sentry/nextjs": "x", "pino": "x", "web-vitals": "x"}}',
    "app/api/login/route.ts": "import { log } from '@/lib/log'\nexport async function POST(req){ log.info({ requestId: req.headers.get('x-request-id') }, 'login') }\n",
    "app/api/health/route.ts": "export const GET = () => Response.json({ ok: true })\n",
    "app/layout.tsx": "import { ConsentBanner } from './consent'\n<script src=\"https://www.googletagmanager.com/gtag/js\"></script>\n",
}


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in obs_check.run(d)}


if __name__ == "__main__":
    got = run_on(BAD)
    want = {"no-error-tracking", "no-structured-logger", "secret-in-log", "console-in-server", "no-request-id",
            "no-health-endpoint", "no-web-vitals", "analytics-no-consent", "no-crash-reporting"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD)
    assert not got, sorted(got)
    print("selftest OK")
