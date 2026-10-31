#!/usr/bin/env python3
"""fe_check: front-end code smells common in AI-generated React/Next.js/React Native/Vue code.

Usage: fe_check.py [root]
Each finding: LEVEL rule path:line  message. Exit 1 on any ERROR.
Silence a line with "fe-check: ignore"; a file with "fe-check: ignore-file".
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

EXT = (".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".turbo", ".expo", "public"}
TEST = re.compile(r"(\.test\.|\.spec\.|__tests__|\.stories\.|e2e/|\.d\.ts$|\.config\.)")

EFFECT_SET = re.compile(r"useEffect\(\s*\(\s*\)\s*=>\s*\{?\s*set[A-Z]\w*\(")
EFFECT_FETCH = re.compile(r"useEffect\(\s*\(\s*\)\s*=>\s*\{[^}]{0,200}?\b(fetch\(|axios\.|\.get\(|supabase\.from\()", re.S)
INDEX_KEY = re.compile(r"key=\{\s*(i|idx|index)\s*\}|:key=\"\s*(i|idx|index)\s*\"")
ANY = re.compile(r":\s*any\b|<any>|as any\b|any\[\]")
TS_IGNORE = re.compile(r"@ts-ignore|@ts-nocheck")
CONSOLE = re.compile(r"\bconsole\.(log|debug)\(")
MAP_NO_KEY = re.compile(r"\.map\(\s*\(?[\w\s,{}]*\)?\s*=>\s*\(?\s*<(?!/)([A-Za-z][\w.]*)(?![^>]*\bkey=)[^>]*>")
INNER_COMPONENT = re.compile(r"^\s{2,}(const|function)\s+[A-Z]\w*\s*(=\s*\([^)]*\)\s*=>|\()")


def walk(root):
    return bk.walk(root, EXT, IGNORE_DIRS)


def is_next(root):
    try:
        with open(os.path.join(root, "package.json"), encoding="utf-8") as f:
            return '"next"' in f.read()
    except OSError:
        return False


def scan(rel, text, next_app, findings):
    if "fe-check: ignore-file" in text or TEST.search(rel):
        return
    lines = text.splitlines()
    jsx = rel.endswith((".tsx", ".jsx"))
    for n, line in enumerate(lines, 1):
        if "fe-check: ignore" in line:
            continue
        add = lambda level, rule, msg: findings.append((level, rule, rel, n, msg))
        if EFFECT_SET.search(line):
            add("WARN", "effect-sets-state", "useEffect that only sets state: derive the value during render (patterns.md §12)")
        if INDEX_KEY.search(line):
            add("WARN", "index-key", "Array index as key breaks state when the list changes: use a stable id")
        if rel.endswith((".ts", ".tsx")) and ANY.search(line) and not line.lstrip().startswith(("//", "*")):
            add("WARN", "any-type", "`any` disables type checking: parse into a typed shape or use unknown")
        if TS_IGNORE.search(line):
            add("ERROR" if "nocheck" in line else "WARN", "ts-ignore", "Type check suppressed: fix the type (or @ts-expect-error with a reason)")
        if CONSOLE.search(line) and not line.lstrip().startswith("//"):
            add("WARN", "console-log", "console.log left in code: remove or use the logger")
        if jsx and MAP_NO_KEY.search(line):
            add("ERROR", "missing-key", "List item rendered from .map without a key")
        if next_app and jsx and re.search(r"<img\b", line):
            add("WARN", "raw-img", "Raw <img> in Next.js: use next/image with width/height (layout shift, size)")
    for m in EFFECT_FETCH.finditer(text):
        n = text[: m.start()].count("\n") + 1
        findings.append(("WARN", "fetch-in-effect", rel, n, "Data fetched in useEffect: use the framework data layer or TanStack Query (race conditions, no cache)"))
    if next_app and re.search(r"(^|/)app/(.*/)?(page|layout)\.(tsx|jsx)$", rel) and re.match(r"\s*['\"]use client['\"]", text):
        findings.append(("WARN", "client-page", rel, 1, "\"use client\" on a page/layout ships the whole route to the browser: move interactivity to a small client child"))
    if jsx:
        depth_fn = 0
        for n, line in enumerate(lines, 1):
            if re.match(r"(export\s+)?(default\s+)?function\s+[A-Z]|(export\s+)?const\s+[A-Z]\w*\s*=", line):
                depth_fn = 1
            elif depth_fn and INNER_COMPONENT.match(line) and "return" not in line:
                findings.append(("WARN", "inner-component", rel, n, "Component defined inside another component remounts every render: move it to module scope"))


def run(root):
    findings = []
    next_app = is_next(root)
    for rel in walk(root):
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
                scan(rel, f.read(), next_app, findings)
        except OSError:
            continue
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "fe_check")


if __name__ == "__main__":
    sys.exit(main())
