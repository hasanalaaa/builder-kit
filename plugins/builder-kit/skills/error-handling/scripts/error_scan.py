#!/usr/bin/env python3
"""error_scan: find swallowed errors, missing timeouts and missing error boundaries.

Usage: error_scan.py [root]
Each finding: LEVEL rule path:line  message. Exit 1 on any ERROR.
Silence a line with a comment containing "error-scan: ignore"; a file with "error-scan: ignore-file".
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

CODE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".swift", ".kt", ".dart")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv",
               "__pycache__", ".turbo", "Pods", ".expo", "android/build", "ios/build"}
TEST = re.compile(bk.TEST_CODE)

JS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
RULES = [
    ("ERROR", "empty-catch", JS + (".dart", ".kt", ".swift"), re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}"),
     "Empty catch swallows the error: handle it or rethrow with context"),
    ("WARN", "bare-except", (".py",), re.compile(r"^\s*except\s*:"), "Bare except also catches KeyboardInterrupt/SystemExit: catch specific exceptions"),
    ("WARN", "catch-log-only", JS, re.compile(r"catch\s*\(\s*(\w+)\s*\)\s*\{\s*console\.(log|error|warn)\([^;]*\);?\s*\}"),
     "Catch only logs and continues: handle, show an error state, or rethrow"),
    ("WARN", "promise-catch-noop", JS, re.compile(r"\.catch\(\s*\(\s*\w*\s*\)\s*=>\s*(\{\s*\}|null|undefined|console\.\w+\([^)]*\))\s*\)"),
     ".catch that ignores the error"),
    ("WARN", "requests-no-timeout", (".py",), re.compile(r"\brequests\.(get|post|put|patch|delete|head|request)\((?![^)]*timeout)"),
     "requests call without timeout= hangs forever on a dead server"),
    ("ERROR", "go-ignored-error", (".go",), re.compile(r"if\s+err\s*!=\s*nil\s*\{\s*\}|^\s*_\s*=\s*err\b"), "Ignored Go error"),
    ("WARN", "swift-try-bang", (".swift",), re.compile(r"\btry!"), "try! crashes on failure: use do/catch"),
    ("WARN", "alert-error-message", JS, re.compile(r"alert\(\s*\w*(err|error|e)\.message"), "Raw error message shown to the user: map to a user message"),
]
FETCH = re.compile(r"\bfetch\(")
FETCH_CHECK = re.compile(r"\.ok\b|\.status\b|fetchWithTimeout|ky\.|ofetch|\$fetch|throwOnError|raise_for_status")
TIMEOUT = re.compile(r"AbortSignal\.timeout|AbortController|signal\s*:|timeout")
HTTPX = re.compile(r"httpx\.(get|post|put|patch|delete|AsyncClient|Client)\((?![^)]*timeout)")


def walk(root):
    return bk.walk(root, CODE_EXT, IGNORE_DIRS)


def scan_file(rel, text, findings):
    if "error-scan: ignore-file" in text:
        return
    test = bool(TEST.search(rel))
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if "error-scan: ignore" in line:
            continue
        for level, rule, exts, rx, msg in RULES:
            if rel.endswith(exts) and rx.search(line):
                findings.append(("WARN" if test else level, rule, rel, n, msg))
        if rel.endswith(".py") and HTTPX.search(line) and not test:
            findings.append(("WARN", "httpx-no-timeout", rel, n, "httpx call without explicit timeout"))
    if rel.endswith(JS) and not test and FETCH.search(text):
        first = next(i for i, l in enumerate(lines, 1) if FETCH.search(l))
        if not FETCH_CHECK.search(text):
            findings.append(("WARN", "fetch-unchecked", rel, first, "fetch() response status never checked (res.ok): non-2xx looks like success"))
        if not TIMEOUT.search(text):
            findings.append(("WARN", "fetch-no-timeout", rel, first, "fetch() without timeout: use AbortSignal.timeout(ms)"))
    multi = re.finditer(r"catch\s*(?:\([^)]*\))?\s*\{\s*\n\s*\}", text) if rel.endswith(JS) else []
    for m in multi:
        n = text[: m.start()].count("\n") + 1
        if "error-scan: ignore" not in lines[n - 1]:
            findings.append(("WARN" if test else "ERROR", "empty-catch", rel, n, "Empty catch swallows the error"))
    if rel.endswith(".py"):
        except_pass_checks(rel, text, lines, test, findings)


# A swallow with a comment on the except/pass line documents a deliberate fallback and is not reported.
EXCEPT_PASS = re.compile(r"^[ \t]*except\b([^:\n]*):[ \t]*(?:\n[ \t]*)?(?:pass|\.\.\.)[ \t]*$", re.M)


def except_pass_checks(rel, text, lines, test, findings):
    for m in EXCEPT_PASS.finditer(text):
        n = text[: m.start()].count("\n") + 1
        if "error-scan: ignore" in lines[n - 1]:
            continue
        broad = re.fullmatch(r"\s*((Base)?Exception)?\s*(as\s+\w+)?\s*", m.group(1)) is not None
        if broad:
            findings.append(("WARN" if test else "ERROR", "except-pass", rel, n, "except: pass swallows every error: handle, log, or rethrow"))
        else:
            findings.append(("WARN", "except-pass-specific", rel, n, f"except{m.group(1)}: pass with no comment: say why ignoring it is safe"))


def repo_checks(root, files, findings):
    has = lambda pat: any(re.search(pat, f) for f in files)
    if has(r"(^|/)app/(.*/)?(page|layout)\.(tsx|jsx)$") and not has(r"(^|/)app/(.*/)?(error|global-error)\.(tsx|jsx)$"):
        findings.append(("WARN", "no-error-boundary", "app/", 0, "Next.js App Router without error.tsx / global-error.tsx"))
    react_spa = has(r"(^|/)src/(main|index)\.(tsx|jsx)$") and not has(r"(^|/)app/")
    if react_spa:
        texts = ""
        for f in files:
            if f.endswith((".tsx", ".jsx")):
                try:
                    with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                        texts += fh.read()
                except OSError:
                    pass  # unreadable file: skip it
        if not re.search(r"ErrorBoundary|componentDidCatch|errorElement", texts):
            findings.append(("WARN", "no-error-boundary", "src/", 0, "React app without an ErrorBoundary / router errorElement"))


def run(root):
    findings = []
    files = walk(root)
    for rel in files:
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
                scan_file(rel, f.read(), findings)
        except OSError:
            continue
    repo_checks(root, files, findings)
    seen, unique = set(), []
    for f in findings:
        if (f[1], f[2], f[3]) not in seen:
            seen.add((f[1], f[2], f[3]))
            unique.append(f)
    return unique


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "error_scan", a.root)


if __name__ == "__main__":
    sys.exit(main())
