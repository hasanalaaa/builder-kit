#!/usr/bin/env python3
"""builder-kit SessionStart hook: a few lines of added context, the repo's repeated lessons plus where the repo map is.

Reads the hook JSON from stdin (cwd, source). On exit 0, plain stdout becomes context Claude sees. Prints nothing
outside a git repo, never prints the map itself (keep the always-on cost ~100 tokens), and exits 0 on any failure.
Disable with BUILDER_KIT_HOOKS=off.
"""
import json
import os
import subprocess
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN, "lib"))
sys.path.insert(0, os.path.join(PLUGIN, "hooks"))
MAP = os.path.join(PLUGIN, "skills", "project-architecture", "scripts", "repo_map.py")
MAX_LESSONS = 5
MAX_LINE = 160


def context(cwd):
    import lessons
    inside = subprocess.run(["git", "-C", cwd, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, timeout=10)
    if inside.returncode != 0:
        return []
    lines = []
    found = lessons.top(cwd, MAX_LESSONS)
    if found:
        lines.append("builder-kit lessons for this repo (mistakes caught here before; avoid repeating them):")
        lines += ["- " + (x if len(x) <= MAX_LINE else x[:MAX_LINE - 1] + "…") for x in found]
    lines.append(f'builder-kit: to learn this repo\'s layout, run `python3 "{MAP}"` (compact file/symbol map, cached) '
                 "before opening many files.")
    return lines


def main():
    try:
        import post_edit
        if post_edit.hooks_off():
            return 0
        data = json.load(sys.stdin)
        lines = context(data.get("cwd") or os.getcwd())
    except (Exception, SystemExit):  # a broken helper must never disturb session start: say nothing
        return 0
    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
