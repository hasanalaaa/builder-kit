#!/usr/bin/env python3
"""Self-test for the PostToolUse hook. Run: python3 test_post_edit.py"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "post_edit.py")


def run_hook(cwd, path, env=None):
    payload = json.dumps({"cwd": cwd, "tool_name": "Write", "tool_input": {"file_path": path}})
    p = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30, env={**os.environ, **(env or {})})
    return p.returncode, p.stderr


def write(d, rel, body):
    path = os.path.join(d, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        bad = write(d, "app/api/pay/route.ts", "const k = 'sk_live_" + "abcdefghijklmnopqrstuvwx'\ntry { x() } catch (e) {}\n")
        code, err = run_hook(d, bad)
        assert code == 2 and "security/" in err and "empty-catch" in err, (code, err)
        ui = write(d, "app/page.tsx", '<h1 className="bg-clip-text text-transparent">Hi</h1>\n<img src="/a.png">\n')
        code, err = run_hook(d, ui)
        assert code == 2 and "gradient-text" in err and "img-alt" in err, (code, err)
        write(d, "package.json", '{"dependencies": {"next-intl": "x"}}')
        rtl = write(d, "app/card.tsx", '<div className="ml-4">x</div>\n')
        code, err = run_hook(d, rtl)
        assert code == 2 and "physical-tailwind" in err, (code, err)
        good = write(d, "app/ok.tsx", 'export default () => <h1 className="ms-4 text-2xl font-semibold">Invoices</h1>\n')
        assert run_hook(d, good)[0] == 0
        assert run_hook(d, bad, {"BUILDER_KIT_HOOKS": "off"})[0] == 0
        assert run_hook(d, os.path.join(d, "missing.ts"))[0] == 0
        nm = write(d, "node_modules/x/index.ts", "try { x() } catch (e) {}\n")
        assert run_hook(d, nm)[0] == 0
    print("selftest OK")
