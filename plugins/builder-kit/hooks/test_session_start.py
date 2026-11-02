#!/usr/bin/env python3
"""Self-test for the SessionStart hook: lessons + map hint, short, silent when off / outside git / broken. Run: python3 test_session_start.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "session_start.py")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import lessons  # noqa: E402


def run(cwd, env=None, raw=None):
    payload = raw if raw is not None else json.dumps({"cwd": cwd, "source": "startup", "hook_event_name": "SessionStart"})
    p = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30, env={**os.environ, **(env or {})})
    assert p.returncode == 0, p
    return p.stdout


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        assert run(d) == "", "outside git: nothing useful to say"
        subprocess.run(["git", "-C", d, "init", "-q"], check=True, capture_output=True)
        out = run(d).splitlines()
        assert len(out) == 1 and "repo_map.py" in out[0] and "lessons" not in out[0], out
        assert os.path.exists(out[0].split('"')[1]), "the map command must point at the real script"

        lessons.add(d, "Money is integer cents")
        for _ in range(2):
            lessons.record(d, [("ERROR", "empty-catch", "a.ts", 2, "x" * 400)])
        for i in range(10):
            lessons.add(d, f"lesson number {i}")
        out = run(d).splitlines()
        assert out[0].startswith("builder-kit lessons for this repo") and len(out) <= 8, out
        assert all(len(x) <= 170 for x in out[1:-1]) and "repo_map.py" in out[-1], out
        assert len("\n".join(out)) < 1000, "always-on cost stays ~100-250 tokens"

        assert run(d, env={"BUILDER_KIT_HOOKS": "off"}) == ""
        assert run(d, raw="not json") == ""
        with open(lessons.store_path(d), "w", encoding="utf-8") as f:
            f.write("[]")
        out = run(d).splitlines()
        assert len(out) == 1 and "repo_map.py" in out[0], "corrupt lessons: still just the map hint"
    print("selftest OK")
