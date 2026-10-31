#!/usr/bin/env python3
"""ship_check: run every relevant builder-kit scanner on a repo and give one SHIP / BLOCKED verdict.

Usage:
  ship_check.py [root] [--only a,b] [--skip a,b] [--report FILE] [--with-tests] [--timeout SEC]
Keys: security architecture errors data tests frontend design a11y rtl ai perf seo release obs legal mobile docs
Exit 1 when any scanner reports ERROR (or fails to run), or when --with-tests and the tests fail.
"""
import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import time

SKILLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "Pods", ".expo"}
SUMMARY = re.compile(r"(\d+) ERROR, (\d+) WARN")
BUILD_HTML_DIRS = ["out", "dist", "build", ".output/public", "public"]


def walk_names(root, limit=20000):
    names = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        names += [os.path.relpath(os.path.join(d, f), root) for f in files]
        if len(names) > limit:
            break
    return names


def project_facts(root):
    names = walk_names(root)
    try:
        with open(os.path.join(root, "package.json"), encoding="utf-8") as f:
            pkg = json.load(f)
    except (OSError, json.JSONDecodeError):
        pkg = {}
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    ui = any(n.endswith((".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss")) for n in names)
    js_ui = any(n.endswith((".tsx", ".jsx", ".vue", ".svelte")) for n in names)
    ai = any(k in deps for k in ("ai", "openai", "@anthropic-ai/sdk", "@google/genai", "langchain", "@ai-sdk/openai", "@ai-sdk/anthropic")) \
        or any(n.endswith(".py") for n in names) and _grep(root, names, r"import (openai|anthropic)|from (openai|anthropic)")
    mobile = "expo" in deps or "react-native" in deps or os.path.exists(os.path.join(root, "pubspec.yaml")) \
        or any(n.endswith(("AndroidManifest.xml", "Info.plist")) for n in names)
    html_dir = next((d for d in BUILD_HTML_DIRS if any(n.startswith(d + "/") and n.endswith(".html") for n in names)
                     or _has_html(os.path.join(root, d))), None)
    return {
        "data": any(n.endswith((".sql", ".prisma")) for n in names),
        "frontend": js_ui, "design": ui, "a11y": ui, "rtl": ui, "legal": ui,
        "ai": bool(ai), "mobile": bool(mobile), "seo_dir": html_dir,
        "perf": bool(pkg) or any(n.lower().endswith((".png", ".jpg", ".jpeg", ".woff2", ".ttf")) for n in names),
        "pkg": pkg,
    }


def _has_html(path):
    if not os.path.isdir(path):
        return False
    for d, _, files in os.walk(path):
        if any(f.endswith(".html") for f in files):
            return True
    return False


def _grep(root, names, pattern):
    rx = re.compile(pattern)
    for n in names:
        if n.endswith(".py"):
            try:
                with open(os.path.join(root, n), encoding="utf-8", errors="ignore") as f:
                    if rx.search(f.read()):
                        return True
            except OSError:
                continue
    return False


def scanners(root, facts):
    """(key, label, script path relative to skills/, args, relevant)"""
    seo_target = [os.path.join(root, facts["seo_dir"])] if facts["seo_dir"] else []
    return [
        ("security", "Security", "launch-security/scripts/security_scan.py", [root], True),
        ("architecture", "Architecture", "project-architecture/scripts/arch_check.py", [root], True),
        ("errors", "Error handling", "error-handling/scripts/error_scan.py", [root], True),
        ("data", "Data model", "data-design/scripts/schema_check.py", [root], facts["data"]),
        ("tests", "Tests", "testing-strategy/scripts/audit_tests.py", [root], True),
        ("frontend", "Front-end code", "frontend-quality/scripts/fe_check.py", [root], facts["frontend"]),
        ("design", "Design craft", "design-system/scripts/design_lint.py", [root], facts["design"]),
        ("a11y", "Accessibility", "accessibility/scripts/a11y_lint.py", [root], facts["a11y"]),
        ("rtl", "RTL / i18n", "i18n-rtl/scripts/rtl_lint.py", [root], facts["rtl"]),
        ("ai", "AI features", "ai-features/scripts/ai_check.py", [root], facts["ai"]),
        ("perf", "Performance", "performance/scripts/perf_budget.py", [root], facts["perf"]),
        ("seo", "SEO", "seo-discoverability/scripts/seo_check.py", seo_target, bool(seo_target)),
        ("release", "Release", "deploy-release/scripts/release_check.py", [root], True),
        ("obs", "Observability", "observability/scripts/obs_check.py", [root], True),
        ("legal", "Legal", "legal-compliance/scripts/legal_check.py", [root], facts["legal"]),
        ("mobile", "Mobile release", "mobile-release/scripts/mobile_release_check.py", [root], facts["mobile"]),
        ("docs", "Docs", "docs-handoff/scripts/docs_check.py", [root], True),
    ]


def run_one(script, args, timeout):
    path = os.path.join(SKILLS, script)
    if not os.path.exists(path):
        return {"status": "missing", "errors": 0, "warns": 0, "output": f"{path} not found", "secs": 0}
    t = time.time()
    try:
        p = subprocess.run([sys.executable, "-I", path, *args], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "errors": 1, "warns": 0, "output": f"timed out after {timeout}s", "secs": timeout}
    out = (p.stdout or "") + (p.stderr or "")
    m = SUMMARY.findall(out)
    errors, warns = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
    status = "ok" if m else ("crashed" if p.returncode not in (0, 1) or "Traceback" in out else "no-summary")
    if status == "crashed":
        errors = max(errors, 1)
    return {"status": status, "errors": errors, "warns": warns, "output": out.strip(), "secs": round(time.time() - t, 1)}


def run_tests(root, pkg, timeout):
    if pkg.get("scripts", {}).get("test"):
        pm = next((pm for lock, pm in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun"))
                   if os.path.exists(os.path.join(root, lock))), "npm")
        cmd = [pm, "test"] if pm != "npm" else ["npm", "test", "--silent"]
    elif any(os.path.exists(os.path.join(root, f)) for f in ("pytest.ini", "conftest.py", "pyproject.toml", "tests")):
        cmd = [sys.executable, "-m", "pytest", "-q"]
    else:
        return {"status": "no-tests", "errors": 0, "warns": 1, "output": "No test command found", "secs": 0}
    t = time.time()
    try:
        p = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=timeout, env={**os.environ, "CI": "1"})
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"status": "failed", "errors": 1, "warns": 0, "output": str(e), "secs": round(time.time() - t, 1)}
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return {"status": "ok" if p.returncode == 0 else "failed", "errors": 0 if p.returncode == 0 else 1, "warns": 0,
            "output": "\n".join(out.splitlines()[-40:]), "secs": round(time.time() - t, 1), "cmd": " ".join(cmd)}


def write_report(path, root, rows, verdict):
    lines = [f"# Ship check: {os.path.abspath(root)}", "", f"**Verdict: {verdict}**", "",
             "| Scanner | Status | ERROR | WARN | Time |", "|---------|--------|-------|------|------|"]
    lines += [f"| {label} | {r['status']} | {r['errors']} | {r['warns']} | {r['secs']}s |" for key, label, r in rows]
    for key, label, r in rows:
        if r["errors"] or r["warns"] or r["status"] not in ("ok",):
            body = "\n".join(r["output"].splitlines()[:80])
            lines += ["", f"## {label}", "", "```", body, "```"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--only", help="comma-separated scanner keys")
    ap.add_argument("--skip", help="comma-separated scanner keys")
    ap.add_argument("--report", help="write a Markdown report to this file")
    ap.add_argument("--with-tests", action="store_true", help="also run the project's test command")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    facts = project_facts(root)
    only = set(a.only.split(",")) if a.only else None
    skip = set(a.skip.split(",")) if a.skip else set()
    selected = [(k, l, s, args) for k, l, s, args, rel in scanners(root, facts)
                if k not in skip and (k in only if only else rel)]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(run_one, s, args, a.timeout): (k, l) for k, l, s, args in selected}
        results = {futures[f]: f.result() for f in concurrent.futures.as_completed(futures)}
    rows = [(k, l, results[(k, l)]) for k, l, s, args in selected]
    if a.with_tests:
        rows.append(("project-tests", "Project tests", run_tests(root, facts["pkg"], a.timeout)))
    total_e = sum(r["errors"] for _, _, r in rows)
    total_w = sum(r["warns"] for _, _, r in rows)
    verdict = "SHIP" if total_e == 0 else "BLOCKED"
    print(f"{'Scanner':18} {'Status':10} {'ERROR':>5} {'WARN':>5}  Time")
    for key, label, r in rows:
        print(f"{label:18} {r['status']:10} {r['errors']:5} {r['warns']:5}  {r['secs']}s")
    print(f"\nship_check: {total_e} ERROR, {total_w} WARN → {verdict}")
    for key, label, r in rows:
        if r["errors"]:
            print(f"\n--- {label} (first lines) ---")
            print("\n".join(r["output"].splitlines()[:15]))
    if a.report:
        write_report(a.report, root, rows, verdict)
        print(f"\nReport written to {a.report}")
    return 0 if verdict == "SHIP" else 1


if __name__ == "__main__":
    sys.exit(main())
