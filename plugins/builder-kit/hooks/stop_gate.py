#!/usr/bin/env python3
"""builder-kit Stop hook: Claude can't end its turn while files it changed this session have blocking findings.

Scans files git reports as modified or new since the session's transcript was created, with the same
per-file scanners and waivers as the edit hook, then runs the project's own typecheck, lint and related tests
on them (project_checks.py; BUILDER_KIT_STOP_CHECKS=off skips that part). Exit 2 (stderr goes back to Claude)
blocks the stop once; on the follow-up stop (stop_hook_active) it never blocks again, so it can't loop.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import post_edit  # noqa: E402
import project_checks  # noqa: E402

MAX_FILES = 60
CHECK_BUDGET = 90  # seconds for project checks; the Stop hook timeout in hooks.json (120) leaves room for the scanners


def stop_checks_off():
    return os.environ.get("BUILDER_KIT_STOP_CHECKS", "on").lower() in ("off", "0", "false", "no")


def session_start(transcript_path):
    try:
        st = os.stat(transcript_path)
        return getattr(st, "st_birthtime", None) or st.st_ctime
    except (OSError, TypeError):
        return 0  # unknown start: consider every changed file


def changed_files(cwd, since):
    out = subprocess.run(["git", "-C", cwd, "status", "--porcelain", "-z", "--untracked-files=all"],
                         capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        return []
    files = []
    for entry in out.stdout.split("\0"):
        if len(entry) < 4 or "D" in entry[:2]:
            continue
        path = os.path.join(cwd, entry[3:])
        try:
            if os.path.getmtime(path) >= since:
                files.append(path)
        except OSError:
            continue  # vanished between status and stat
    return files[:MAX_FILES]


def main():
    if post_edit.hooks_off():
        return 0
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if data.get("stop_hook_active"):
        return 0
    cwd = data.get("cwd") or os.getcwd()
    try:
        report = []
        files = changed_files(cwd, session_start(data.get("transcript_path")))
        for path in files:
            result = post_edit.blocking_errors(path, cwd)
            if result and result[1]:
                report += post_edit.describe(*result, limit=6)
        checks = [] if stop_checks_off() else project_checks.run(cwd, files, CHECK_BUDGET)
    except (Exception, SystemExit) as e:  # a broken guardrail must never trap the session
        print(f"builder-kit stop gate skipped: {type(e).__name__}: {e}", file=sys.stderr)
        return 0
    if not report and not checks:
        return 0
    print("\n".join(["builder-kit: not done yet. Files you changed this session still have blocking issues:"] + report + checks
                    + ["Fix them, re-check, then finish." + (" " + post_edit.WAIVER_HINT if report else "")]), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
