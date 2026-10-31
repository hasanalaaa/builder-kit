"""Shared helpers for builder-kit scanners: repo file listing, waivers, and the standard findings report."""
import collections
import fnmatch
import json
import os
import re
import subprocess

CONFIG = ".builder-kit.json"
RULES = r"(?::\s*([\w-]+(?:\s*,\s*[\w-]+)*))?"
INLINE = re.compile(r"bk-ignore(?!-file)" + RULES)
INLINE_FILE = re.compile(r"bk-ignore-file" + RULES)
WHERE_LINE = re.compile(r"^(.+?):(\d+)$")
KEYS = ("level", "rule", "path", "line", "message")
# Test code in every ecosystem builder-kit scans; scanners add their own extras (stories, fixtures, configs...).
TEST_CODE = (r"\.test\.|\.spec\.|(?:^|/)(?:__tests__|tests?|spec|e2e|src/test|androidTest|testFixtures)/|(?:^|/)test_\w+\.py$"
             r"|_test\.(?:py|go|dart)$|Tests?\.(?:swift|kt|java)$")


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


def normalize(f):
    """Any scanner's finding tuple → (level, rule, path, line, message); path '.' means repo-wide."""
    if len(f) == 6:  # security_scan: level, check number, rule, path, line, message
        return f[0], f[2], f[3], f[4] or 0, f"[{f[1]}] {f[5]}"
    if len(f) == 5:
        return f[0], f[1], f[2], f[3] or 0, f[4]
    if len(f) == 4:
        m = WHERE_LINE.match(str(f[2]))
        return (f[0], f[1], m.group(1), int(m.group(2)), f[3]) if m else (f[0], f[1], str(f[2]), 0, f[3])
    return f[0], f[1], ".", 0, f[2]


def load_config(root):
    """Read .builder-kit.json; a broken file stops the scan instead of silently waiving nothing (or everything)."""
    path = os.path.join(root, CONFIG)
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        raise SystemExit(f"{path}: {e}")
    ignore = cfg.get("ignore", {}) if isinstance(cfg, dict) else None
    if not isinstance(ignore, dict) or not all(isinstance(v, list) and all(isinstance(g, str) for g in v) for v in ignore.values()):
        raise SystemExit(f'{path}: "ignore" must map a rule name (or "*") to a list of path globs')
    return cfg


def _listed(match, rule):
    return bool(match) and (not match.group(1) or rule in {r.strip() for r in match.group(1).split(",")})


def waived(root, cfg, finding, lines_cache):
    """True when .builder-kit.json or a bk-ignore comment waives this normalized finding."""
    _, rule, path, line, _ = finding
    ignore = cfg.get("ignore", {})
    if any(fnmatch.fnmatch(path, g) for key in (rule, "*") for g in ignore.get(key, [])):
        return True
    if path == "." or not root:
        return False
    if path not in lines_cache:
        lines = read(root, path).splitlines()
        lines_cache[path] = lines, [m for m in map(INLINE_FILE.search, lines) if m]
    lines, file_waivers = lines_cache[path]
    if any(_listed(m, rule) for m in file_waivers):
        return True
    return any(0 < n <= len(lines) and _listed(INLINE.search(lines[n - 1]), rule) for n in (line, line - 1))


def report(findings, name, root, cap=30, note=""):
    """Print findings ERROR-first (JSON lines when BUILDER_KIT_FORMAT=json) after waivers; return the exit code."""
    cfg, cache = (load_config(root) if root else {}), {}
    rows = [normalize(f) for f in findings]
    kept = [f for f in rows if not waived(root, cfg, f, cache)]
    as_json = os.environ.get("BUILDER_KIT_FORMAT") == "json"
    counts = collections.Counter()
    for f in sorted(kept, key=lambda f: (f[0] != "ERROR", f[1], f[2], f[3])):
        if as_json:
            print(json.dumps(dict(zip(KEYS, f)), ensure_ascii=False))
            continue
        counts[f[1]] += 1
        if counts[f[1]] <= cap:
            print(f"{f[0]:5} {f[1]:22} {f[2]}{':' + str(f[3]) if f[3] else ''}  {f[4]}")
    for rule, c in counts.items():
        if c > cap:
            print(f"      {rule}: {c - cap} more")
    errors = sum(f[0] == "ERROR" for f in kept)
    waived_note = f" · {len(rows) - len(kept)} waived" if len(rows) > len(kept) else ""
    print(f"\n{name}: {errors} ERROR, {len(kept) - errors} WARN{note}{waived_note}")
    return 1 if errors else 0
