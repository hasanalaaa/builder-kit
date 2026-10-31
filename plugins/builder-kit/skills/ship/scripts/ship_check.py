#!/usr/bin/env python3
"""ship_check: run every relevant builder-kit scanner on a repo and give one SHIP / BLOCKED verdict.

Usage:
  ship_check.py [root] [--only a,b] [--skip a,b] [--report FILE] [--json FILE] [--sarif FILE] [--with-tests] [--timeout SEC]
Keys: security architecture errors data tests frontend design a11y rtl ai perf seo release obs legal mobile docs
Exit 1 when any scanner reports ERROR (or fails to run), or when --with-tests and the tests fail.
Waivers: a `bk-ignore[: rule,...]` comment on (or above) a line, `bk-ignore-file[: rule,...]` in a file,
or .builder-kit.json at the root: {"ignore": {"<rule>|*": ["<path glob>", ...]}} (* crosses folders, "." = repo-wide).
"""
import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

SKILLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "Pods", ".expo"}
SUMMARY = re.compile(r"(\d+) ERROR, (\d+) WARN")
REPO_URL = "https://github.com/hasanalaaa/builder-kit"
BUILD_HTML_DIRS = ["out", "dist", "build", ".output/public", "public"]


def walk_names(root):
    return bk.walk(root, ignore=SKIP_DIRS)


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
        p = subprocess.run([sys.executable, "-I", path, *args], capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "BUILDER_KIT_FORMAT": "json"})
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "errors": 1, "warns": 0, "output": f"timed out after {timeout}s", "secs": timeout, "findings": []}
    findings, text = split_json((p.stdout or "") + (p.stderr or ""))
    out = "\n".join(text)
    m = SUMMARY.findall(out)
    errors, warns = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
    status = "ok" if m else ("crashed" if p.returncode not in (0, 1) or "Traceback" in out else "no-summary")
    if status == "crashed":
        errors = max(errors, 1)
    return {"status": status, "errors": errors, "warns": warns, "output": out.strip(), "secs": round(time.time() - t, 1),
            "findings": findings, "text": text}


def dedupe(rows):
    """Drop findings an earlier scanner already reported (same rule, path, line), then rebuild counts and output."""
    seen = set()
    for _, _, r in rows:
        if "text" not in r:
            continue
        keys = [(f["rule"], f["path"], f["line"]) for f in r["findings"]]
        fresh = [f for f, k in zip(r["findings"], keys) if k not in seen]
        seen.update(keys)
        dropped = len(r["findings"]) - len(fresh)
        r["findings"] = fresh
        if r["status"] == "ok":
            r["errors"] = sum(f["level"] == "ERROR" for f in fresh)
            r["warns"] = len(fresh) - r["errors"]
        note = [f"({dropped} duplicate finding(s) already reported by an earlier scanner)"] if dropped else []
        r["output"] = "\n".join([format_finding(f) for f in fresh] + [t for t in r["text"] if not SUMMARY.search(t)] + note).strip()


def split_json(out):
    """Scanner output in BUILDER_KIT_FORMAT=json mode → (finding dicts, the other lines)."""
    findings, text = [], []
    for line in out.splitlines():
        if line.startswith('{"level"'):
            try:
                findings.append(json.loads(line))
                continue
            except json.JSONDecodeError:
                pass  # not a finding after all: keep it as text
        text.append(line)
    return findings, text


def format_finding(f):
    return f"{f['level']:5} {f['rule']:22} {f['path']}{':' + str(f['line']) if f['line'] else ''}  {f['message']}"


def run_tests(root, pkg, timeout):
    if pkg.get("scripts", {}).get("test"):
        pm = next((pm for lock, pm in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun"))
                   if os.path.exists(os.path.join(root, lock))), "npm")
        cmd = [pm, "test"] if pm != "npm" else ["npm", "test", "--silent"]
    elif any(os.path.exists(os.path.join(root, f)) for f in ("pytest.ini", "conftest.py", "pyproject.toml", "tests")):
        cmd = [sys.executable, "-m", "pytest", "-q"]
    elif re.search(r"(?m)^test:", _read(os.path.join(root, "Makefile"))):
        cmd = ["make", "test"]
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


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""  # missing file: treated as empty


def all_findings(rows, facts):
    """Every finding with its scanner key and a repo-relative path (SEO paths are relative to the built site)."""
    found = []
    for key, _, r in rows:
        for f in r.get("findings", []):
            path = f["path"]
            if key == "seo" and facts["seo_dir"] and path != "." and "://" not in path:
                path = f"{facts['seo_dir']}/{path}"
            found.append({**f, "scanner": key, "path": path})
    return found


def write_sarif(path, root, findings):
    """SARIF 2.1.0 for GitHub code scanning; repo-wide findings anchor to README.md (code scanning needs a file)."""
    anchor = next((n for n in ("README.md", "readme.md", "README") if os.path.exists(os.path.join(root, n))), None)
    try:  # code scanning resolves URIs from the repo root, which may sit above the scanned folder
        prefix = subprocess.run(["git", "-C", root, "rev-parse", "--show-prefix"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        prefix = ""  # not a git checkout: paths stay relative to the scanned folder
    results, rules = [], {}
    for f in findings:
        rule_id = f"{f['scanner']}/{f['rule']}"
        rules.setdefault(rule_id, {"id": rule_id, "shortDescription": {"text": f["rule"]}, "helpUri": REPO_URL})
        uri = f["path"] if f["path"] != "." else anchor
        if not uri or "://" in uri:
            continue
        results.append({"ruleId": rule_id, "level": "error" if f["level"] == "ERROR" else "warning",
                        "message": {"text": f["message"]},
                        "locations": [{"physicalLocation": {"artifactLocation": {"uri": prefix + uri, "uriBaseId": "%SRCROOT%"},
                                                            "region": {"startLine": f["line"] or 1}}}]})
    doc = {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
           "runs": [{"tool": {"driver": {"name": "builder-kit", "informationUri": REPO_URL, "rules": list(rules.values())}},
                     "results": results}]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)


def write_json(path, root, rows, verdict, findings):
    doc = {"root": root, "verdict": verdict,
           "scanners": [{"key": k, "label": label, "status": r["status"], "errors": r["errors"], "warns": r["warns"], "secs": r["secs"]}
                        for k, label, r in rows],
           "findings": findings}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)


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
    ap.add_argument("--json", help="write every finding as JSON to this file (for agents and dashboards)")
    ap.add_argument("--sarif", help="write SARIF 2.1.0 to this file (GitHub code scanning annotations)")
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
    dedupe(rows)
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
    if a.json or a.sarif:
        findings = all_findings(rows, facts)
        if a.json:
            write_json(a.json, root, rows, verdict, findings)
        if a.sarif:
            write_sarif(a.sarif, root, findings)
    return 0 if verdict == "SHIP" else 1


if __name__ == "__main__":
    sys.exit(main())
