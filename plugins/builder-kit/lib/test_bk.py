#!/usr/bin/env python3
"""Self-test for bk: tuple normalization, waivers (inline, file, config) and JSON output. Run: python3 test_bk.py"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bk  # noqa: E402


def write(d, rel, body):
    os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
    with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
        f.write(body)


def run_report(findings, root, env=None):
    old = os.environ.pop("BUILDER_KIT_FORMAT", None)
    os.environ.update(env or {})
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            code = bk.report(findings, "t", root)
    finally:
        os.environ.pop("BUILDER_KIT_FORMAT", None)
        if old is not None:
            os.environ["BUILDER_KIT_FORMAT"] = old
    return code, out.getvalue()


if __name__ == "__main__":
    assert bk.normalize(("ERROR", "07", "xss", "a.ts", 3, "m")) == ("ERROR", "xss", "a.ts", 3, "[07] m")
    assert bk.normalize(("WARN", "r", "a.sql:12", "m")) == ("WARN", "r", "a.sql", 12, "m")
    assert bk.normalize(("WARN", "r", "a.sql", "m")) == ("WARN", "r", "a.sql", 0, "m")
    assert bk.normalize(("WARN", "r", "m")) == ("WARN", "r", ".", 0, "m")
    is_test = lambda p: bool(re.search(bk.TEST_CODE, p))
    for p in ("android/app/src/test/java/A.kt", "ios/AppTests/LoginTests.swift", "pkg/x_test.go", "a/b.spec.ts",
              "tests/test_a.py", "e2e/run.mjs", "__tests__/x.js", "app/src/androidTest/B.kt", "lib/a_test.dart"):
        assert is_test(p), p
    for p in ("src/testing.ts", "contest/a.ts", "src/latest.ts", "app/test-utils-impl.ts"):
        assert not is_test(p), p
    with tempfile.TemporaryDirectory() as d:
        write(d, "a.ts", "x()  // bk-ignore: empty-catch -- reviewed\n// bk-ignore\ny()\nz()\n")
        write(d, "fixture.ts", "// bk-ignore-file: secret\nk()\n")
        f = lambda rule, path, line: ("ERROR", rule, path, line, "m")
        code, out = run_report([f("empty-catch", "a.ts", 1)], d)
        assert code == 0 and "1 waived" in out, out
        assert run_report([f("other", "a.ts", 1)], d)[0] == 1          # comment names another rule
        assert run_report([f("anything", "a.ts", 3)], d)[0] == 0       # bare bk-ignore on the line above
        assert run_report([f("anything", "a.ts", 4)], d)[0] == 1
        assert run_report([f("secret", "fixture.ts", 2)], d)[0] == 0   # file-level waiver for one rule
        assert run_report([f("xss", "fixture.ts", 2)], d)[0] == 1
        write(d, bk.CONFIG, json.dumps({"ignore": {"no-changelog": ["."], "*": ["vendor/*"]}}))
        assert run_report([f("no-changelog", ".", 0), f("x", "vendor/a/b.js", 9)], d)[0] == 0
        assert run_report([f("no-runbooks", ".", 0)], d)[0] == 1
        code, out = run_report([f("x", "src/a.ts", 2)], d, {"BUILDER_KIT_FORMAT": "json"})
        first = json.loads(out.splitlines()[0])
        assert first == {"level": "ERROR", "rule": "x", "path": "src/a.ts", "line": 2, "message": "m"}, first
        assert "1 ERROR, 0 WARN" in out
        for bad in ("{broken", '{"ignore": {"x": "a/*"}}', "[]"):
            write(d, bk.CONFIG, bad)
            try:
                bk.load_config(d)
                raise AssertionError(f"accepted {bad}")
            except SystemExit:
                pass  # expected: a broken config fails loudly
    print("selftest OK")
