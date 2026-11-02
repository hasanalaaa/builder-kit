#!/usr/bin/env python3
"""Self-test for lessons.py: record/top/add, once-per-run counting, caps, corrupt file, no git, CLI. Run: python3 test_lessons.py"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lessons  # noqa: E402

CATCH = ("ERROR", "empty-catch", "app/api/x/route.ts", 3, "empty catch swallows the error")

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        assert lessons.store_path(d) is None
        lessons.record(d, [CATCH])
        assert lessons.add(d, "x") is False and lessons.top(d) == [] and os.listdir(d) == [], "no git: no-op"

        subprocess.run(["git", "-C", d, "init", "-q"], check=True, capture_output=True)
        store = lessons.store_path(d)
        assert store == os.path.join(os.path.realpath(d), ".git", "builder-kit", "lessons.json"), store
        lessons.record(d, [CATCH, CATCH[:3] + (9, "second hit, same run"), ("ERROR", "hardcoded-secret", "a.ts", 1, "key")])
        assert lessons.top(d) == [], "one run is not a repeat"
        lessons.record(d, [("WARN", "empty-catch", "lib/y.ts:7", "four-tuple shape")])
        top = lessons.top(d)
        assert top == ["empty-catch caught 2x (last lib/y.ts:7: four-tuple shape)"], top
        assert lessons.add(d, "  Use the  shared fetch client  ") and lessons.add(d, "Use the shared fetch client")
        assert lessons.add(d, "Money is integer cents") and not lessons.add(d, "   ")
        top = lessons.top(d)
        assert top[:2] == ["Money is integer cents", "Use the shared fetch client"] and len(top) == 3, top
        assert len(lessons.top(d, n=1)) == 1
        git_status = subprocess.run(["git", "-C", d, "status", "--porcelain"], capture_output=True, text=True).stdout
        assert git_status == "", "nothing to commit or gitignore"

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            lessons.record(d, [("broken",)])  # malformed finding: reported, never raised
        assert "lessons skipped" in err.getvalue()

        lessons.record(d, [("ERROR", f"rule-{i}", "f", 0, "m") for i in range(lessons.MAX_RULES + 50)])
        with open(store, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["rules"]) == lessons.MAX_RULES and "empty-catch" in data["rules"], "cap keeps the frequent rules"

        with open(store, "w", encoding="utf-8") as f:
            f.write("{not json")
        assert lessons.top(d) == [] and os.path.exists(store + ".corrupt"), "corrupt file is moved aside"
        lessons.record(d, [CATCH])
        lessons.record(d, [CATCH])
        assert lessons.top(d) == ["empty-catch caught 2x (last app/api/x/route.ts:3: empty catch swallows the error)"]

        cli = lambda *a: subprocess.run([sys.executable, os.path.join(HERE, "lessons.py"), *a, "--cwd", d], capture_output=True, text=True)
        assert cli("add", "Run make check before done").returncode == 0
        out = cli("list").stdout
        assert "Run make check before done" in out and "empty-catch" in out, out
        assert cli("clear").returncode == 0 and not os.path.exists(store) and lessons.top(d) == []
        assert cli("add").returncode != 0
    with tempfile.TemporaryDirectory() as d:
        assert subprocess.run([sys.executable, os.path.join(HERE, "lessons.py"), "list", "--cwd", d], capture_output=True).returncode == 1
    print("selftest OK")
