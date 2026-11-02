#!/usr/bin/env python3
"""Self-test for the Stop gate: blocks on changed files with ERRORs, never loops, ignores old changes. Run: python3 test_stop_gate.py"""
import json
import os
import subprocess
import sys
import tempfile
import time

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stop_gate.py")


def run(cwd, transcript, active=False, env=None):
    payload = json.dumps({"cwd": cwd, "transcript_path": transcript, "stop_hook_active": active})
    p = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=60,
                       env={**os.environ, **(env or {})})
    return p.returncode, p.stderr


def write(d, rel, body):
    path = os.path.join(d, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        git = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, check=True)
        git("init", "-q")
        old = write(d, "legacy/old.ts", "try { x() } catch (e) {}\n")  # dirty before the session started
        time.sleep(1.1)
        transcript = write(d, ".session/t.jsonl", "{}\n")
        assert run(d, transcript)[0] == 0, "pre-session changes must not block"
        time.sleep(1.1)
        write(d, "app/api/x/route.ts", "export async function GET() { try { await go() } catch (e) {} }\n")
        code, err = run(d, transcript)
        assert code == 2 and "empty-catch" in err and "route.ts" in err and "old.ts" not in err, (code, err)
        assert run(d, transcript, active=True)[0] == 0, "must never block twice in a row"
        assert run(d, transcript, env={"BUILDER_KIT_HOOKS": "off"})[0] == 0
        write(d, "app/api/x/route.ts", "export async function GET() { await go() }\n")
        assert run(d, transcript)[0] == 0, "clean change must pass"
        assert run(os.path.join(d, "nope"), transcript)[0] == 0, "non-repo cwd must pass"
        assert os.path.exists(old)

    with tempfile.TemporaryDirectory() as d:  # project checks: a fake tsc that reports a type error in a changed file
        subprocess.run(["git", "-C", d, "init", "-q"], capture_output=True, check=True)
        write(d, ".gitignore", "node_modules/\n")
        write(d, "tsconfig.json", "{}\n")
        tsc = write(d, "node_modules/.bin/tsc", "#!/bin/sh\necho \"src/x.ts(1,7): error TS2322: Type 'string' is not assignable"
                                               " to type 'number'.\"\necho \"src/old.ts(1,1): error TS2304: old\"\nexit 2\n")
        os.chmod(tsc, 0o755)
        transcript = write(d, ".session/t.jsonl", "{}\n")
        now = time.time()
        for rel in (".gitignore", "tsconfig.json"):  # explicit mtimes instead of sleeps: before and after the session start
            os.utime(os.path.join(d, rel), (now - 100, now - 100))
        x = write(d, "src/x.ts", "export const x: number = 'a'\n")
        os.utime(x, (now + 10, now + 10))
        code, err = run(d, transcript)
        assert code == 2 and "[typecheck: tsc --noEmit]" in err and "TS2322" in err and "old.ts" not in err, (code, err)
        assert "bk-ignore" not in err, "the waiver hint is only for scanner findings"
        assert run(d, transcript, active=True)[0] == 0, "must never block twice in a row"
        assert run(d, transcript, env={"BUILDER_KIT_STOP_CHECKS": "off"})[0] == 0
        assert run(d, transcript, env={"BUILDER_KIT_HOOKS": "off"})[0] == 0
    print("selftest OK")
