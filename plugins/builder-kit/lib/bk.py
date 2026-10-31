"""Shared helpers for builder-kit scanners: repo file listing and the standard findings report."""
import collections
import os
import subprocess


def walk(root, exts=None, ignore=frozenset(), dot_dirs=False):
    """Relative repo paths ('/' separated), honoring .gitignore in git repos, filtered by extension and ignored dirs."""
    keep = lambda f: (exts is None or f.endswith(tuple(exts))) and not set(f.split("/")) & set(ignore)
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True, timeout=30)
        if out.returncode == 0 and out.stdout.strip():
            return sorted(filter(keep, out.stdout.splitlines()))
    except (OSError, subprocess.SubprocessError):
        pass  # not a git repo or git missing: fall back to walking the tree
    found = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in ignore and (dot_dirs or not x.startswith("."))]
        found += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in files]
    return sorted(filter(keep, found))


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""  # unreadable file: scanners treat it as empty


def report(findings, name, cap=30, note=""):
    """Print findings ERROR-first (5-tuples level, rule, path, line, msg or 4-tuples level, rule, where, msg); return exit code."""
    counts = collections.Counter()
    for f in sorted(findings, key=lambda f: (f[0] != "ERROR", f[1], str(f[2]), f[3] if len(f) == 5 else 0)):
        level, rule, where = f[0], f[1], f[2]
        if len(f) == 5 and f[3]:
            where = f"{where}:{f[3]}"
        counts[rule] += 1
        if counts[rule] <= cap:
            print(f"{level:5} {rule:22} {where}  {f[-1]}")
    for rule, c in counts.items():
        if c > cap:
            print(f"      {rule}: {c - cap} more")
    errors = sum(f[0] == "ERROR" for f in findings)
    print(f"\n{name}: {errors} ERROR, {len(findings) - errors} WARN{note}")
    return 1 if errors else 0
