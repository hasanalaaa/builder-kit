#!/usr/bin/env python3
"""Self-test for ship_check: runs the real scanners on a tiny project. Run: python3 test_ship_check.py"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SHIP = os.path.join(HERE, "ship_check.py")


def make(d, files):
    for rel, body in files.items():
        os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
        with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
            f.write(body)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        make(d, {
            "package.json": '{"dependencies": {"next": "x"}}',
            "app/page.tsx": "export default function P(){ return <img src='/a.png'/> }\n",
            "app/api/x/route.ts": "const KEY = 'sk_live_" + "abcdefghijklmnopqrstuvwx'\nexport function GET(){ try { a() } catch (e) {} }\n",
        })
        report = os.path.join(d, "SHIP_REPORT.md")
        p = subprocess.run([sys.executable, SHIP, d, "--report", report], capture_output=True, text=True, timeout=600)
        out = p.stdout + p.stderr
        assert p.returncode == 1, out
        assert "BLOCKED" in out, out
        for label in ("Security", "Error handling", "Accessibility", "Release", "Docs"):
            assert label in out, (label, out)
        assert "crashed" not in out and "missing" not in out, out
        with open(report, encoding="utf-8") as f:
            assert "Verdict: BLOCKED" in f.read()
        p = subprocess.run([sys.executable, SHIP, d, "--only", "docs"], capture_output=True, text=True, timeout=120)
        assert "Docs" in p.stdout and "Security" not in p.stdout, p.stdout
    print("selftest OK")
