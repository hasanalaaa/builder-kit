#!/usr/bin/env python3
"""audit_tests: check that a repo's tests exist, run, and can actually fail.

Usage: audit_tests.py [root] [--modules DIR]   (DIR default: auto = src/features, features, app, src, lib)
Findings: no tests, no test script, focused tests (.only/fit/fdescribe), skipped tests, sleeps in tests,
tests without assertions, trivially true assertions, source modules without any test mentioning them.
Exit 1 on any ERROR. A test file containing "test-audit: ignore-file" is skipped.
"""
# test-audit: ignore-file
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "__pycache__", ".turbo"}
TEST = re.compile(r"(\.test\.|\.spec\.|(^|/)__tests__/|(^|/)tests?/|(^|/)test_[\w]+\.py$|_test\.(py|go)$|Tests?\.swift$|e2e/)")
CODE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".go", ".swift", ".kt", ".dart")
FOCUSED = re.compile(r"\b(it|test|describe|context)\.only\(|\b(fit|fdescribe)\(|@pytest\.mark\.only|test\.describe\.only\(")
SKIPPED = re.compile(r"\b(it|test|describe)\.(skip|todo)\(|\b(xit|xdescribe|xtest)\(|@pytest\.mark\.skip\b|@unittest\.skip|t\.Skip\(")
SLEEP = re.compile(r"waitForTimeout\(|\bsetTimeout\(\s*r\w*\s*,\s*\d{3,}|time\.sleep\(|Thread\.sleep\(|\bsleep\(\d")
TRIVIAL = re.compile(r"expect\(\s*(true|1)\s*\)\.(toBe|toEqual)\(\s*(true|1)\s*\)|assert\s+True\b|assertTrue\(\s*True\s*\)|expect\(true\)\.toBeTruthy")
ASSERT = re.compile(r"\bexpect\(|\bassert\b|\bassert\w*\(|\.should\(|toHaveBeenCalled|\bXCTAssert|#expect\(|t\.(Error|Fatal|Fail)")
TEST_BLOCK = re.compile(r"^\s*(?:it|test)\(\s*['\"`]([^'\"`]+)|^\s*def (test_\w+)|^\s*func (Test\w+)", re.M)


def walk(root):
    return bk.walk(root, None, IGNORE_DIRS)


read = bk.read


def blocks_without_assert(text):
    """Yield names of test blocks whose body (until the next test block) has no assertion."""
    starts = list(TEST_BLOCK.finditer(text))
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        if not ASSERT.search(text[m.end():end]):
            yield next(g for g in m.groups() if g), text[: m.start()].count("\n") + 1


def has_test_script(root, files):
    pkg = read(root, "package.json")
    if pkg:
        try:
            if json.loads(pkg).get("scripts", {}).get("test", "").strip() not in ("", 'echo "Error: no test specified" && exit 1'):
                return True
        except json.JSONDecodeError:
            pass  # invalid package.json: treat as no scripts
    return any(re.search(r"(^|/)(pytest\.ini|conftest\.py|vitest\.config|jest\.config|playwright\.config|go\.mod|Package\.swift)", f) for f in files) \
        or "[tool.pytest" in read(root, "pyproject.toml")


def module_dirs(root, files, explicit):
    bases = [explicit] if explicit else ["src/features", "features", "src/modules", "modules", "app", "src", "lib"]
    for base in bases:
        subs = sorted({f[len(base) + 1:].split("/")[0] for f in files if f.startswith(base + "/") and f.count("/") > base.count("/") + 1})
        subs = [s for s in subs if not s.startswith(("_", ".", "(")) and s not in ("api", "components", "styles", "public", "assets")]
        if subs:
            return base, subs
    return None, []


def run(root, modules=None):
    files = walk(root)
    tests = [f for f in files if f.endswith(CODE) and TEST.search(f)]
    findings = []
    if not tests:
        findings.append(("ERROR", "no-tests", ".", 0, "No test files found: start with one integration test of the main flow (testing-strategy §2)"))
    if not has_test_script(root, files):
        findings.append(("WARN", "no-test-script", ".", 0, "No test command/config found (package.json \"test\", pytest config, vitest/jest/playwright config)"))
    test_text = {}
    for rel in tests:
        text = test_text[rel] = read(root, rel)
        if "test-audit: ignore-file" in text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if FOCUSED.search(line):
                findings.append(("ERROR", "focused-test", rel, n, ".only / fit runs one test and silently skips the rest"))
            if SKIPPED.search(line):
                findings.append(("WARN", "skipped-test", rel, n, "Skipped test: fix it or delete it with a reason"))
            if SLEEP.search(line):
                findings.append(("WARN", "sleep-in-test", rel, n, "Fixed sleep makes tests slow and flaky: wait for a condition"))
            if TRIVIAL.search(line):
                findings.append(("ERROR", "trivial-assert", rel, n, "Assertion that can never fail"))
        for name, n in blocks_without_assert(text):
            findings.append(("WARN", "no-assertion", rel, n, f"Test '{name}' has no assertion"))
    base, mods = module_dirs(root, files, modules)
    blob = "\n".join(test_text.values()).lower() + "\n" + "\n".join(tests).lower()
    for mod in mods:
        if mod.lower() not in blob:
            findings.append(("WARN", "untested-module", f"{base}/{mod}", 0, "No test file mentions this module"))
    return findings, len(tests)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--modules", help="directory whose subfolders are feature modules")
    a = p.parse_args()
    findings, n = run(a.root, a.modules)
    return bk.report(findings, "audit_tests", note=f" ({n} test files)")


if __name__ == "__main__":
    sys.exit(main())
