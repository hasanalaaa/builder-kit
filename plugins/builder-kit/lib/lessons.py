#!/usr/bin/env python3
"""Per-repo lessons memory: which gate rules keep firing here, plus free-text lessons, surfaced at session start.

Stored in <git-common-dir>/builder-kit/lessons.json: outside the working tree (nothing to commit or gitignore) and shared
by every worktree of the repo. No git → every call is a no-op. A corrupt file is moved aside and started fresh.
CLI: python3 lessons.py list | add "text" | clear [--cwd DIR]
"""
import argparse
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bk  # noqa: E402

MAX_RULES = 200
MAX_MANUAL = 30
MAX_TEXT = 200


def store_path(cwd):
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None  # git missing: no memory
    return os.path.join(out.stdout.strip(), "builder-kit", "lessons.json") if out.returncode == 0 else None


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("rules"), dict) and isinstance(data.get("manual"), list):
            return data
    except FileNotFoundError:
        return {"rules": {}, "manual": []}
    except (OSError, ValueError):
        pass  # unreadable or corrupt: moved aside below
    try:
        os.replace(path, path + ".corrupt")  # keep the bad copy for a human, start clean
    except OSError:
        pass  # can't move it either: the next save overwrites it
    return {"rules": {}, "manual": []}


def save(path, data):
    rules = data["rules"]
    if len(rules) > MAX_RULES:  # keep the most frequent, most recent rules
        keep = sorted(rules, key=lambda r: (rules[r].get("count", 0), rules[r].get("last", "")), reverse=True)[:MAX_RULES]
        data["rules"] = {r: rules[r] for r in keep}
    data["manual"] = data["manual"][-MAX_MANUAL:]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)  # atomic: a reader never sees half a file


def _today():
    return datetime.date.today().isoformat()


def record(cwd, findings):
    """Count each rule once per call (one gate run) with its latest example. Never raises: it runs inside hooks.

    findings: scanner tuples in any shape bk.normalize accepts, normally (level, rule, path, line, message)."""
    try:
        path = store_path(cwd)
        if not path or not findings:
            return
        # ponytail: read-modify-write without a lock; two sessions stopping at the same instant can lose one count.
        data = load(path)
        seen = {}
        for f in findings:
            level, rule, where, line, message = bk.normalize(tuple(f))
            seen[str(rule)] = (level, f"{where}:{line}" if line else str(where), str(message)[:MAX_TEXT])
        for rule, (level, where, message) in seen.items():
            row = data["rules"].setdefault(rule, {"count": 0, "first": _today()})
            row.update(count=int(row.get("count") or 0) + 1, last=_today(), level=level, path=where, message=message)
        save(path, data)
    except Exception as e:  # memory is a nice-to-have: report, never break the gate that called us
        print(f"builder-kit lessons skipped: {type(e).__name__}: {e}", file=sys.stderr)


def add(cwd, text):
    """Store a free-text lesson; returns False outside git or for empty text."""
    path, text = store_path(cwd), " ".join(str(text).split())[:MAX_TEXT]
    if not path or not text:
        return False
    data = load(path)
    data["manual"] = [m for m in data["manual"] if m.get("text") != text] + [{"text": text, "date": _today()}]
    save(path, data)
    return True


def top(cwd, n=5):
    """At most n lines: manual lessons (newest first), then rules the gates caught in 2+ runs (most frequent first)."""
    path = store_path(cwd)
    if not path or not os.path.exists(path):
        return []
    data = load(path)
    lines = [m["text"] for m in reversed(data["manual"]) if isinstance(m, dict) and m.get("text")]
    rules = sorted(((r, v) for r, v in data["rules"].items() if isinstance(v, dict) and isinstance(v.get("count"), int) and v["count"] >= 2),
                   key=lambda rv: (-rv[1]["count"], rv[0]))
    lines += [f"{r} caught {v['count']}x (last {v.get('path', '?')}: {v.get('message', '')})" for r, v in rules]
    return lines[:n]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=("list", "add", "clear"))
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--cwd", default=".")
    a = p.parse_args()
    path = store_path(a.cwd)
    if not path:
        print("lessons: not inside a git repo, nothing stored", file=sys.stderr)
        return 1
    if a.action == "add":
        if not add(a.cwd, a.text):
            p.error("add needs the lesson text")
        print("lesson saved")
    elif a.action == "clear":
        if os.path.exists(path):
            os.remove(path)
        print("lessons cleared")
    else:
        data = load(path) if os.path.exists(path) else {"rules": {}, "manual": []}
        for m in data["manual"]:
            print(f"lesson  {m.get('date', '')}  {m.get('text', '')}")
        for r, v in sorted(data["rules"].items(), key=lambda rv: -rv[1].get("count", 0)):
            print(f"rule    {v.get('count', 0):3}x  {r}  last {v.get('last', '')} {v.get('path', '')}: {v.get('message', '')}")
        if not data["manual"] and not data["rules"]:
            print("no lessons yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
