#!/usr/bin/env python3
"""repo_map: a compact map of a repo (one line per source file with its key symbols) to read instead of opening files.

Usage: repo_map.py [root] [--max-tokens N] [--refresh]
Header: stack, entry points, folders with file counts. Body: files grouped by folder with exports, functions, classes,
Next.js routes (+ HTTP methods), SQL tables, Prisma models, Go/Swift/Kotlin/Dart types. Honors .gitignore; skips
vendored, generated, lock and asset files. Fits a token budget (~4 chars/token) by collapsing big folders first.
Cached in <git-dir>/builder-kit/map.txt, keyed by file mtimes; outside git it is rebuilt every time.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ai-workflow", "scripts"))
import bk  # noqa: E402
import context_pack  # noqa: E402

SKIP_DIRS = {"node_modules", "vendor", "third_party", "dist", "build", ".next", "out", "coverage", ".venv", "venv", "Pods",
             ".expo", ".dart_tool", "target", "DerivedData", "generated", "__generated__", "__pycache__", ".git", "worktrees"}
GENERATED = re.compile(r"\.min\.js$|\.d\.ts$|\.(?:g|freezed|pb|generated)\.\w+$|_pb2\.py$|\.pb\.go$")
MAX_BYTES = 300_000
MANIFESTS = (("package.json", "Node"), ("pyproject.toml", "Python"), ("requirements.txt", "Python"), ("go.mod", "Go"),
             ("Cargo.toml", "Rust"), ("pubspec.yaml", "Flutter/Dart"), ("Package.swift", "Swift package"),
             ("build.gradle.kts", "Gradle/Kotlin"), ("build.gradle", "Gradle"), ("supabase/config.toml", "Supabase"),
             ("prisma/schema.prisma", "Prisma"), ("Dockerfile", "Docker"))
ENTRY = {"main.py", "__main__.py", "manage.py", "app.py", "main.go", "main.ts", "main.tsx", "main.js", "index.ts", "index.tsx",
         "index.js", "server.ts", "server.js", "layout.tsx", "_layout.tsx", "main.dart", "App.tsx", "Main.kt", "MainActivity.kt"}
PER_FILE = 6  # symbols shown per file before "+N"
CAPS = (40, 15, 8, 4, 2, 1)  # files shown per folder, tried in order until the map fits the budget
DEPTHS = (99, 6, 5, 4, 3, 2, 1)  # then folders deeper than this fold into a count

EXPORT = re.compile(r"^export\s+(?:default\s+)?(?:declare\s+)?(?:async\s+)?(?:abstract\s+)?"
                    r"(?:function\*?|class|const|let|var|interface|type|enum)\s+(\w+)", re.M)
EXPORT_LIST = re.compile(r"^export\s*\{([^}]*)\}", re.M)
CJS = re.compile(r"^(?:module\.)?exports\.(\w+)\s*=", re.M)
METHOD = re.compile(r"^export\s+(?:async\s+)?(?:function\s+|const\s+)(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", re.M)
NEXT_ROUTE = re.compile(r"(?:^|/)app/(.*?)/?(route|page)\.[jt]sx?$")
PATTERNS = {
    ".py": re.compile(r"^(?:async\s+)?(?:def|class)\s+([A-Za-z]\w*)", re.M),
    ".go": re.compile(r"^(?:func\s+(?:\([^)]*\)\s*)?|type\s+)([A-Z]\w*)", re.M),
    ".swift": re.compile(r"^(?:\s*(?:public|open|internal|final|@\w+)\s+)*(?:class|struct|enum|protocol|actor)\s+(\w+)", re.M),
    ".kt": re.compile(r"^(?:(?:public|internal|data|sealed|abstract|open|enum|annotation)\s+)*(?:class|interface|object)\s+(\w+)", re.M),
    ".dart": re.compile(r"^(?:(?:abstract|sealed|final|base)\s+)*(?:class|mixin|enum|extension)\s+(\w+)", re.M),
    ".sql": re.compile(r"\bcreate\s+table\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)", re.I),
    ".prisma": re.compile(r"^model\s+(\w+)", re.M),
}
JS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
SOURCE = JS + tuple(PATTERNS) + (".kts",)


def symbols(rel, text):
    """Key names a reader needs from one file; a Next.js route/page becomes its URL plus HTTP methods."""
    ext = os.path.splitext(rel)[1]
    if ext in JS:
        route = NEXT_ROUTE.search(rel)
        if route:
            url = "/" + "/".join(p for p in route.group(1).split("/") if p and not p.startswith("("))
            methods = list(dict.fromkeys(METHOD.findall(text)))
            return [(",".join(methods) + " " + url).strip() if route.group(2) == "route" else "page " + url]
        names = EXPORT.findall(text) + CJS.findall(text)
        for group in EXPORT_LIST.findall(text):
            names += [n.split(" as ")[-1].strip() for n in group.split(",") if n.strip()]
    else:
        names = [n.strip('"') for n in PATTERNS[".kt" if ext == ".kts" else ext].findall(text)]
    return list(dict.fromkeys(names))


def source_files(root, all_files):
    return [f for f in all_files if f.endswith(SOURCE) and not GENERATED.search(f) and os.path.isfile(os.path.join(root, f))]


def stack(root):
    """Stack names from root manifests only (context_pack's tables; its full detect() walks the whole tree)."""
    found = [label for f, label in MANIFESTS if os.path.exists(os.path.join(root, f))]
    try:
        pkg = json.loads(bk.read(root, "package.json") or "{}")
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    except (ValueError, AttributeError):
        deps = {}  # broken package.json: no JS stack hints
    found += [label for k, label in context_pack.JS_FRAMEWORKS + context_pack.JS_TOOLS if k in deps]
    py = bk.read(root, "pyproject.toml") + bk.read(root, "requirements.txt")
    found += [label for k, label in context_pack.PY_FRAMEWORKS if py and re.search(rf"\b{k}\b", py, re.I)]
    return list(dict.fromkeys(found))


def header(root, files, all_files):
    entry = [f for f in all_files if f.count("/") <= 2 and os.path.basename(f) in ENTRY][:8]
    counts = {}
    for f in all_files:
        parts = f.split("/")
        if len(parts) > 1:
            key = "/".join(parts[:2]) if len(parts) > 2 else parts[0]
            counts[key] = counts.get(key, 0) + 1
    dirs = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
    lines = [f"# repo map: {os.path.basename(os.path.abspath(root))} ({len(files)} source files of {len(all_files)})"]
    names = stack(root)
    if names:
        lines.append("stack: " + ", ".join(names))
    if entry:
        lines.append("entry: " + ", ".join(entry))
    if dirs:
        lines.append("dirs: " + ", ".join(f"{d}/ {c}" for d, c in sorted(dirs)))
    return lines


def collapse(groups, depth):
    """Folders deeper than `depth` fold into their ancestor as a count: (folder, entries, tests, hidden files, hidden folders)."""
    out = {}
    for d, (entries, tests) in groups.items():
        parts = d.split("/")
        if d == "." or len(parts) <= depth:
            out.setdefault(d, [[], [], 0, set()])[:2] = entries, tests
        else:
            row = out.setdefault("/".join(parts[:depth]), [[], [], 0, set()])
            row[2] += len(entries) + len(tests)
            row[3].add(d)
    return sorted(out.items())


def render(head, rows, cap, budget):
    """Map text with at most `cap` files per folder; past the budget, the rest is summarized as 'N more files in X'."""
    lines, size, rest = list(head), sum(len(x) + 1 for x in head), {}
    for d, (entries, tests, hidden, subdirs) in rows:
        block = [f"{d}/"]
        for name, syms in entries[:cap]:
            more = f" +{len(syms) - PER_FILE}" if len(syms) > PER_FILE else ""
            block.append(f"  {name}" + (": " + " ".join(syms[:PER_FILE]) + more if syms else ""))
        if len(entries) > cap:
            block.append(f"  … {len(entries) - cap} more files")
        if tests:
            block.append("  tests: " + " ".join(tests[:cap]) + (f" +{len(tests) - cap}" if len(tests) > cap else ""))
        if hidden:
            block.append(f"  … {hidden} files in {len(subdirs)} subfolders")
        cost = sum(len(x) + 1 for x in block)
        if rest or size + cost > budget - 300:  # room for the "N more files in X" line
            rest[d] = len(entries) + len(tests) + hidden
            continue
        lines += block
        size += cost
    if rest:
        top = sorted(rest.items(), key=lambda kv: -kv[1])[:6]
        lines.append(f"… {sum(rest.values())} more files in " + ", ".join(f"{d}/ ({n})" for d, n in top)
                     + (f" and {len(rest) - 6} more folders" if len(rest) > 6 else ""))
    return "\n".join(lines), not rest


def build(root, all_files, max_tokens):
    files = source_files(root, all_files)
    groups = {}
    for rel in files:
        d, name = os.path.split(rel)
        entries, tests = groups.setdefault(d or ".", ([], []))
        if re.search(bk.TEST_CODE, rel):
            tests.append(name)
            continue
        text = "" if os.path.getsize(os.path.join(root, rel)) > MAX_BYTES else bk.read(root, rel)
        entries.append((name, symbols(rel, text)))
    head = header(root, files, all_files)
    # Shallower folders before fewer files per folder: a huge repo gets an overview, not the first few folders in full.
    for depth in DEPTHS:
        rows = collapse(groups, depth)
        for cap in CAPS:
            text, fits = render(head, rows, cap, max_tokens * 4)
            if fits:
                return text
    return text


def cache_path(root):
    try:
        out = subprocess.run(["git", "-C", root, "rev-parse", "--absolute-git-dir"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None  # no git: no cache
    return os.path.join(out.stdout.strip(), "builder-kit", "map.txt") if out.returncode == 0 else None


def cache_key(root, all_files, max_tokens):
    h = hashlib.sha1(f"{os.path.realpath(root)} {max_tokens} {os.path.getmtime(__file__)}".encode())
    for rel in all_files:
        try:
            st = os.stat(os.path.join(root, rel))
        except OSError:
            continue  # listed by git but deleted from the tree
        h.update(f"{rel}\0{st.st_mtime_ns}\0{st.st_size}\n".encode())
    return h.hexdigest()


def repo_map(root, max_tokens=2500, refresh=False):
    path, all_files = cache_path(root), bk.walk(root, ignore=SKIP_DIRS)
    key = cache_key(root, all_files, max_tokens) if path else None
    if path and not refresh:
        try:
            with open(path, encoding="utf-8") as f:
                first, _, body = f.read().partition("\n")
            if first == key:
                return body
        except OSError:
            pass  # no cache yet: build it
    text = build(root, all_files, max_tokens)
    if path:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path + ".tmp", "w", encoding="utf-8") as f:
                f.write(key + "\n" + text)
            os.replace(path + ".tmp", path)
        except OSError as e:  # read-only git dir: the map is still printed, just not cached
            print(f"repo_map: cache not written: {e}", file=sys.stderr)
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--max-tokens", type=int, default=2500)
    p.add_argument("--refresh", action="store_true", help="ignore the cache and rebuild")
    a = p.parse_args()
    if not os.path.isdir(a.root):
        p.error(f"not a directory: {a.root}")
    print(repo_map(a.root, max(a.max_tokens, 200), a.refresh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
