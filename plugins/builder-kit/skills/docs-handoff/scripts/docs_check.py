#!/usr/bin/env python3
"""docs_check: are the project docs present, complete and consistent with the code?

Usage: docs_check.py [root]
Checks: README and its sections, CLAUDE.md/AGENTS.md, ARCHITECTURE.md, .env.example coverage, CHANGELOG, runbooks,
package scripts mentioned in docs but missing from package.json. Exit 1 on any ERROR.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "__pycache__", ".turbo", ".expo"}
README_SECTIONS = {
    "setup": r"install|setup|getting started|quick ?start|التثبيت|البدء",
    "run": r"\bdev\b|run|start|تشغيل",
    "test": r"test|اختبار",
    "deploy": r"deploy|release|production|النشر",
    "env": r"\.env|environment variables|env vars|متغيرات",
}
CMD = re.compile(r"\b(?:npm run|pnpm(?: run)?|yarn(?: run)?|bun run)\s+([a-zA-Z][\w:.-]*)")
PM_BUILTINS = {"install", "add", "remove", "dlx", "exec", "i", "ci", "run", "create", "init", "update", "upgrade", "outdated", "audit", "why",
               "link", "publish", "test", "start", "x", "global", "up", "store", "env", "config", "list", "ls", "prune", "dev"}
ENV_USE = re.compile(r"process\.env\.([A-Z][A-Z0-9_]+)|import\.meta\.env\.([A-Z][A-Z0-9_]+)|os\.environ(?:\.get)?\(\s*['\"]([A-Z][A-Z0-9_]+)|os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]+)")
BUILTIN_ENV = {"NODE_ENV", "CI", "PORT", "VERCEL", "VERCEL_ENV", "VERCEL_URL", "NEXT_RUNTIME", "MODE", "DEV", "PROD", "SSR", "BASE_URL", "TZ", "HOME", "PATH", "DEBUG"}


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def all_files(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in IGNORE_DIRS and not x.startswith(".")]
        out += [os.path.relpath(os.path.join(d, f), root) for f in files]
    return out


def run(root):
    files = all_files(root)
    findings = []
    readme = next((f for f in ("README.md", "readme.md", "README") if f in files), None)
    if not readme:
        findings.append(("ERROR", "no-readme", ".", "No README.md: a new developer can't start"))
        text = ""
    else:
        text = read(root, readme)
        if len(text.strip()) < 300 or "This is a [Next.js]" in text or "bootstrapped with" in text:
            findings.append(("WARN", "readme-boilerplate", readme, "README is empty or framework boilerplate"))
        for name, rx in README_SECTIONS.items():
            if not re.search(rx, text, re.I):
                findings.append(("WARN", f"readme-no-{name}", readme, f"README doesn't cover {name}"))
    if not any(f in files for f in ("CLAUDE.md", "AGENTS.md", ".cursorrules")) and not any(f.startswith(".cursor/rules") for f in files):
        findings.append(("WARN", "no-agent-context", ".", "No CLAUDE.md/AGENTS.md: draft one with ai-workflow/scripts/context_pack.py"))
    code_files = [f for f in files if f.endswith((".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".swift", ".kt", ".dart"))]
    if len(code_files) > 30 and "ARCHITECTURE.md" not in files and not any(f.endswith("architecture.md") for f in files):
        findings.append(("WARN", "no-architecture", ".", "No ARCHITECTURE.md project map (project-architecture skill)"))
    if "CHANGELOG.md" not in files:
        findings.append(("WARN", "no-changelog", ".", "No CHANGELOG.md"))
    if not any(re.search(r"(^|/)(runbooks?|playbooks?)/|runbook", f, re.I) for f in files):
        findings.append(("WARN", "no-runbooks", ".", "No runbooks (deploy, rollback, incident, restore, key rotation)"))
    try:
        scripts = json.loads(read(root, "package.json") or "{}").get("scripts", {})
    except json.JSONDecodeError:
        scripts = {}
    if scripts or "package.json" in files:
        docs = [f for f in files if f.endswith(".md") and not f.startswith(("node_modules", "CHANGELOG"))]
        for doc in docs:
            for m in CMD.finditer(read(root, doc)):
                name = m.group(1)
                if name not in scripts and name not in PM_BUILTINS:
                    findings.append(("ERROR", "doc-command-missing", doc, f"Docs mention '{m.group(0)}' but package.json has no '{name}' script"))
    used = set()
    for f in code_files:
        if not re.search(r"(\.test\.|\.spec\.|__tests__|/tests?/|(^|/)test_\w+\.py$)", f):
            for m in ENV_USE.finditer(read(root, f)):
                used.add(next(g for g in m.groups() if g))
    used -= BUILTIN_ENV | set(re.findall(r"\b[A-Z][A-Z0-9_]{3,}\b", text))
    example = next((f for f in files if re.search(r"(^|/)\.env\.(example|sample|template)$", f)), None)
    if used and not example:
        findings.append(("ERROR", "no-env-example", ".", f"Code reads {len(used)} env vars; no .env.example documents them"))
    elif example:
        documented = set(re.findall(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]+)\s*=", read(root, example), re.M))
        missing, stale = sorted(used - documented), sorted(documented - used)
        if missing:
            findings.append(("WARN", "env-undocumented", example, "Not documented: " + ", ".join(missing[:10])))
        if stale and used:
            findings.append(("WARN", "env-stale", example, "Documented but unused in code: " + ", ".join(stale[:10])))
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "docs_check", a.root)


if __name__ == "__main__":
    sys.exit(main())
