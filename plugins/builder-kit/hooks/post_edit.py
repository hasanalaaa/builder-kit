#!/usr/bin/env python3
"""builder-kit PostToolUse hook: scan the file Claude just wrote with the fast builder-kit scanners.

Reads the hook JSON from stdin. Only ERROR-level findings block (exit 2: stderr goes back to Claude);
everything else passes silently. Disable with BUILDER_KIT_HOOKS=off.
"""
import collections
import json
import os
import re
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(PLUGIN, "skills")
for d in ("launch-security", "error-handling", "design-system", "accessibility", "i18n-rtl"):
    sys.path.insert(0, os.path.join(SKILLS, d, "scripts"))
sys.path.insert(0, os.path.join(PLUGIN, "lib"))
import bk  # noqa: E402

SKIP_PARTS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "Pods", ".expo"}
UI = (".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss")
MARKUP = (".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html")
MAX_BYTES = 1_000_000
I18N_HINT = re.compile(r"next-intl|i18next|react-intl|vue-i18n|@nuxtjs/i18n|paraglide|lingui|expo-localization")


def rtl_project(cwd):
    try:
        with open(os.path.join(cwd, "package.json"), encoding="utf-8") as f:
            if I18N_HINT.search(f.read()):
                return True
    except OSError:
        pass  # unreadable file: skip it
    return any(os.path.exists(os.path.join(cwd, p)) for p in ("messages/ar.json", "locales/ar", "public/locales/ar", "src/locales/ar.json", "i18n/ar.json"))


def collect(rel, text, cwd):
    errors = []
    import security_scan
    security_scan.findings.clear()
    security_scan.scan_file(rel, text)
    errors += [("security", rule, line, msg) for lvl, chk, rule, _, line, msg in security_scan.findings if lvl == "ERROR"]
    import error_scan
    found = []
    error_scan.scan_file(rel, text, found)
    errors += [("error-scan", rule, line, msg) for lvl, rule, _, line, msg in found if lvl == "ERROR"]
    if rel.endswith(UI):
        import design_lint
        found = []
        design_lint.scan_file(rel, text, found, collections.defaultdict(collections.Counter))
        errors += [("design-lint", rule, line, msg) for lvl, rule, _, line, msg in found if lvl == "ERROR"]
    if rel.endswith(MARKUP):
        import a11y_lint
        found = []
        a11y_lint.element_checks(rel, text, found)
        a11y_lint.icon_button_checks(rel, text, found)
        errors += [("a11y-lint", rule, line, msg) for lvl, rule, _, line, msg in found if lvl == "ERROR"]
    if rel.endswith(UI + (".ts", ".js")) and rtl_project(cwd):
        import rtl_lint
        found = []
        rtl_lint.scan(rel, text, False, found)
        errors += [("rtl-lint", rule, line, msg) for lvl, rule, _, line, msg in found if lvl == "ERROR"]
    return errors


def main():
    if os.environ.get("BUILDER_KIT_HOOKS", "on").lower() in ("off", "0", "false", "no"):
        return 0
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    cwd = data.get("cwd") or os.getcwd()
    if not path or not os.path.isfile(path) or os.path.getsize(path) > MAX_BYTES:
        return 0
    rel = os.path.relpath(path, cwd) if os.path.abspath(path).startswith(os.path.abspath(cwd) + os.sep) else os.path.basename(path)
    if set(rel.split(os.sep)) & SKIP_PARTS:
        return 0
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        cfg, cache = bk.load_config(cwd), {rel: (text.splitlines(), [m for m in map(bk.INLINE_FILE.search, text.splitlines()) if m])}
        errors = [e for e in collect(rel, text, cwd) if not bk.waived(cwd, cfg, ("ERROR", e[1], rel, e[2] or 0, e[3]), cache)]
    except (Exception, SystemExit) as e:  # a broken guardrail (or a broken .builder-kit.json) must never block the user's work
        print(f"builder-kit hook skipped: {type(e).__name__}: {e}", file=sys.stderr)
        return 0
    if not errors:
        return 0
    lines = [f"builder-kit found {len(errors)} blocking issue(s) in {rel}:"]
    lines += [f"- [{tool}/{rule}] line {line}: {msg}" for tool, rule, line, msg in errors[:12]]
    if len(errors) > 12:
        lines.append(f"- … {len(errors) - 12} more")
    lines.append("Fix them now. If one is a false positive, put `bk-ignore: <rule> -- <reason>` in a comment on that line "
                 "(or the line above); for a whole folder use .builder-kit.json {\"ignore\": {\"<rule>\": [\"<glob>\"]}}.")
    print("\n".join(lines), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
