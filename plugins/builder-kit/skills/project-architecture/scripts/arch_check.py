#!/usr/bin/env python3
"""Architecture fitness check for any repo (stdlib only).

Finds the structural signatures of tangled code: oversized files, import cycles
(JS/TS + Python), cross-feature internal imports, shared/ depending on features,
duplicated blocks, junk-drawer and versioned-copy file names, commented-out code,
crowded and deeply nested folders.

Also measures functions: length, parameter count and nesting depth (exact for
Python via ast; a brace-counting heuristic for JS/TS).

Usage:  arch_check.py [ROOT] [--stats] [--max-lines 500] [--warn-lines 300] [--max-function 50]
                      [--max-params 4] [--max-nesting 3] [--dup-lines 8]
Exit code 1 when any ERROR is found. Tests: python3 test_arch_check.py --stats adds size metrics for before/after comparisons.
"""
import argparse
import ast
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".py", ".go", ".rb",
              ".php", ".java", ".kt", ".swift", ".dart", ".rs", ".cs"}
JS_EXT = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".output",
               "coverage", "vendor", ".venv", "venv", "env", "__pycache__", "Pods", ".expo", "DerivedData",
               "target", ".turbo", ".cache", "generated", "__generated__", ".dart_tool", ".gradle", "bin", "obj",
               "third_party", "third-party", "thirdparty", "external", "extern", "managed_components", ".pio"}
FEATURE_ROOTS = {"features", "modules", "domains"}
SHARED_ROOTS = {"shared", "lib", "common", "core"}
JUNK_NAMES = {"utils", "util", "helpers", "helper", "misc", "common", "stuff", "general", "other", "temp", "tmp"}
VERSIONED = re.compile(r"([_\-. ](v\d+|new|old|copy|backup|bak|final|fixed|tmp|temp|orig)|\s\(\d+\)|\scopy)$", re.I)
CODE_KEYWORD = re.compile(r"^(const|let|var|return|import|export|def|class|function|if|for|while|elif|else|try|except|print|console\.)\b.*[(){}=;:\[\]]")
CODE_ASSIGN = re.compile(r"""^[\w.$\[\]]+\s*(=|\+=|-=)\s*[\w"'\[{(].*[;)\]}"'\w]$""")
CODE_CALL = re.compile(r"^[\w.$]+\(.*\)\s*;?$")
PROSE = re.compile(r"[A-Za-z]{2,}\s+[a-z]{2,}\s+[a-z]{2,}\s+[a-z]{2,}")
TRIVIAL = {"}", "};", "});", "})", "];", ")", ");", "end", "else {", "} else {", "return;", "pass", "break;", "*/", "/**", "{", "]"}

findings = []
stats = {}


def report(level, rule, path, line, msg):
    findings.append((level, rule, path, line, msg))


# --- function metrics -------------------------------------------------------

NEST_BLOCKS = tuple(getattr(ast, n) for n in ("If", "For", "AsyncFor", "While", "With", "AsyncWith", "Try", "TryStar", "Match")
                    if hasattr(ast, n))
JS_FN = re.compile(
    r"\bfunction\b[^(]*\(([^)]*)\)"                                   # function f(a, b) {
    r"|\(([^()]*)\)\s*(?::\s*[^=]+)?=>\s*\{\s*$"                       # (a, b) => {
    r"|^\s*(?:(?:public|private|protected|static|async|get|set)\s+)*"  # method(a, b) {
    r"(?!(?:if|for|while|switch|catch|with|return|else)\b)[A-Za-z_$][\w$]*\s*\(([^)]*)\)\s*(?::\s*[^{]+)?\{\s*$")
JS_STRIP = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`|//.*$")


def record_function(rel, line, length, params, depth, args):
    stats["functions"] = stats.get("functions", 0) + 1
    stats["function_lines"] = stats.get("function_lines", 0) + length
    if length > args.max_function:
        stats["long_functions"] = stats.get("long_functions", 0) + 1
        report("WARN", "function-too-long", rel, line, f"{length} lines (budget {args.max_function}); split by responsibility")
    if params is not None and params > args.max_params:
        report("WARN", "too-many-params", rel, line, f"{params} parameters (budget {args.max_params}); pass an options object")
    if depth is not None and depth > args.max_nesting:
        report("WARN", "deep-code-nesting", rel, line, f"nesting depth {depth} (budget {args.max_nesting}); use guard clauses or extract")


def py_nesting(node, depth=0):
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue  # nested functions are measured on their own
        is_elif = isinstance(node, ast.If) and isinstance(child, ast.If) and node.orelse == [child]
        step = 1 if isinstance(child, NEST_BLOCKS) and not is_elif else 0
        best = max(best, py_nesting(child, depth + step))
    return best


def check_functions(rel, lines, args):
    if is_test(rel):
        return  # test bodies are long by nature; budgets apply to production code
    if rel.endswith(".py"):
        try:
            tree = ast.parse("\n".join(lines))
        except (SyntaxError, ValueError):
            return
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                a = node.args
                params = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs if x.arg not in ("self", "cls")]
                record_function(rel, node.lineno, node.end_lineno - node.lineno + 1, len(params), py_nesting(node), args)
    elif rel.endswith(tuple(JS_EXT)):
        # ponytail: brace counting, not a parser; multi-line signatures and braces in regex literals can skew it.
        for i, line in enumerate(lines):
            m = JS_FN.search(line) if line.rstrip().endswith("{") else None
            if not m:
                continue
            depth = 0
            for j in range(i, len(lines)):
                code = JS_STRIP.sub("", lines[j])
                depth += code.count("{") - code.count("}")
                if depth <= 0:
                    raw = next((g for g in m.groups() if g is not None), "")
                    params = None if "{" in raw or "[" in raw else len([p for p in raw.split(",") if p.strip()])
                    record_function(rel, i + 1, j - i + 1, params, None, args)
                    break


def looks_like_code(s):
    if CODE_KEYWORD.match(s) or s.endswith((";", "{", "}")) or CODE_CALL.match(s):
        return True
    return bool(CODE_ASSIGN.match(s)) and not PROSE.search(s)


def keep(rel):
    parts = rel.split(os.sep)
    name = parts[-1]
    return (os.path.splitext(name)[1] in SOURCE_EXT and not name.endswith((".min.js", ".d.ts"))
            and ".generated." not in name
            and not any(p in IGNORE_DIRS or p.startswith(".") for p in parts[:-1]))


def walk(root):
    # Prefer Git's file list so .gitignore'd output never counts.
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "-co", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout
        return sorted(f for f in (os.path.normpath(x) for x in out.splitlines() if x) if keep(f))
    except (OSError, subprocess.CalledProcessError):
        pass  # not a git repo: fall back to os.walk
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for f in filenames:
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            if keep(rel):
                files.append(rel)
    return sorted(files)


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return []


def is_test(rel):
    name = os.path.basename(rel)
    return ".test." in name or ".spec." in name or name.startswith("test_") or "/tests/" in f"/{rel}" or "__tests__" in rel


# --- per-file checks -------------------------------------------------------

def check_file(rel, lines, args):
    n = len(lines)
    if n > args.max_lines:
        report("WARN" if is_test(rel) else "ERROR", "file-too-long", rel, 0, f"{n} lines (limit {args.max_lines}); split by responsibility")
    elif n > args.warn_lines:
        report("WARN", "file-long", rel, 0, f"{n} lines (budget {args.warn_lines})")

    stem = os.path.splitext(os.path.basename(rel))[0]
    stem = re.sub(r"\.(test|spec)$", "", stem)
    if VERSIONED.search(stem):
        report("ERROR", "versioned-copy", rel, 0, "version/copy suffix in file name; edit the original, Git is the archive")
    if stem.lower() in JUNK_NAMES and n > 150:
        report("WARN", "junk-drawer", rel, 0, f"'{stem}' file with {n} lines; move each function to the module that owns it")

    prefix = "#" if rel.endswith((".py", ".rb")) else "//"
    run_start, run = 0, 0
    for i, line in enumerate(lines + [""], 1):
        s = line.strip()
        if s.startswith(prefix) and looks_like_code(s[len(prefix):].strip()):
            if run == 0:
                run_start = i
            run += 1
        else:
            if run >= 5:
                report("WARN", "commented-out-code", rel, run_start, f"{run} consecutive lines of commented-out code; delete it")
            run = 0


def check_dirs(root, files):
    per_dir = defaultdict(int)
    for f in files:
        per_dir[os.path.dirname(f)] += 1
        depth = f.count(os.sep)
        # JVM package paths (src/main/java/com/acme/...) are deep by convention.
        if depth > 8 and not f.endswith((".java", ".kt", ".scala")):
            report("WARN", "deep-nesting", f, 0, f"{depth} folders deep")
    for d, count in per_dir.items():
        if count > 25:
            report("WARN", "crowded-folder", d or ".", 0, f"{count} source files in one folder; group by feature")
        if os.path.basename(d).lower() in JUNK_NAMES and count > 8:
            report("WARN", "junk-drawer", d, 0, f"'{os.path.basename(d)}/' folder with {count} files")


# --- import graph -----------------------------------------------------------

JS_IMPORT = re.compile(r"""(?:^|\s)(?:import|export)\s+(?!type\s)(?:[^'"]*?\s+from\s+)?['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)|import\(\s*['"]([^'"]+)['"]\s*\)""")
PY_FROM = re.compile(r"^\s*from\s+(\.*)([\w.]*)\s+import\s+(.+)")
PY_IMPORT = re.compile(r"^\s*import\s+([\w.]+)")


def resolve_js(rel, spec, fileset, alias_base):
    if spec.startswith("."):
        base = os.path.normpath(os.path.join(os.path.dirname(rel), spec))
    elif spec.startswith(("@/", "~/")):
        base = os.path.normpath(os.path.join(alias_base, spec[2:]))
    else:
        return None
    for cand in [base] + [base + e for e in JS_EXT] + [os.path.join(base, "index" + e) for e in JS_EXT]:
        if cand in fileset:
            return cand
    return None


def resolve_py_module(parts_base, mod, fileset):
    path = os.path.join(parts_base, *mod.split(".")) if mod else parts_base
    for cand in (path + ".py", os.path.join(path, "__init__.py")):
        cand = os.path.normpath(cand)
        if cand in fileset:
            return cand
    return None


def py_line_targets(rel, line, fileset, py_roots):
    """Files one Python import line points to: relative imports and absolute imports of in-repo packages."""
    m = PY_FROM.match(line)
    if m and m.group(1):
        base = os.path.dirname(rel)
        for _ in range(len(m.group(1)) - 1):
            base = os.path.dirname(base)
        if m.group(2):
            return [resolve_py_module(base, m.group(2), fileset)]
        # from . import a, b  -> the submodules a and b
        return [resolve_py_module(base, n, fileset) for n in re.split(r"[,\s()]+", m.group(3)) if n.isidentifier()]
    plain = PY_IMPORT.match(line)
    mod = m.group(2) if m else (plain.group(1) if plain else "")
    top = mod.split(".")[0]
    return [resolve_py_module(py_roots[top], mod, fileset)] if top in py_roots else []


def imports_of(rel, lines, fileset, alias_base, py_roots):
    if rel.endswith(tuple(JS_EXT) + (".vue", ".svelte")):
        targets = [resolve_js(rel, m.group(1) or m.group(2) or m.group(3), fileset, alias_base)
                   for line in lines if not line.lstrip().startswith(("import type", "export type"))
                   for m in JS_IMPORT.finditer(line)]
    elif rel.endswith(".py"):
        targets = [t for line in lines for t in py_line_targets(rel, line, fileset, py_roots)]
    else:
        return []
    return [t for t in targets if t and t != rel]


def find_cycles(graph):
    index, low, on, stack, sccs, counter = {}, {}, set(), [], [], [0]
    sys.setrecursionlimit(max(10000, len(graph) * 4))

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                sccs.append(sorted(comp))

    for v in list(graph):
        if v not in index:
            strong(v)
    return sccs


def area(rel):
    """Return ('feature', name, rest) / ('shared', name, rest) / (None, ...) for a path."""
    parts = rel.split(os.sep)
    for i, p in enumerate(parts[:-1]):
        if p in FEATURE_ROOTS and i + 1 < len(parts) - 1:
            return "feature", "/".join(parts[: i + 2]), "/".join(parts[i + 2:])
        if p in SHARED_ROOTS:
            return "shared", "/".join(parts[: i + 1]), "/".join(parts[i + 1:])
    return None, None, None


def is_front_door(rest):
    return os.path.splitext(rest)[0] in ("index", "__init__", "mod", "public-api")


def check_imports(root, files, contents):
    fileset = set(files)
    alias_base = "src" if os.path.isdir(os.path.join(root, "src")) else ""
    py_roots = {}
    for base in ("", "src"):
        bdir = os.path.join(root, base)
        if os.path.isdir(bdir):
            for name in os.listdir(bdir):
                if os.path.isfile(os.path.join(bdir, name, "__init__.py")):
                    py_roots.setdefault(name, base)
    graph = {}
    for rel in files:
        targets = imports_of(rel, contents[rel], fileset, alias_base, py_roots)
        graph[rel] = set(targets)
        kind_a, name_a, _ = area(rel)
        for t in set(targets):
            kind_b, name_b, rest_b = area(t)
            if kind_b == "feature" and name_b != name_a and not is_front_door(rest_b):
                report("ERROR", "feature-internal-import", rel, 0, f"imports {t}; go through {name_b}'s index/front door")
            if kind_a == "shared" and kind_b == "feature":
                report("ERROR", "shared-imports-feature", rel, 0, f"shared code imports feature code ({t}); invert the dependency")
    for comp in find_cycles(graph):
        shown = " -> ".join(comp[:6]) + (" ..." if len(comp) > 6 else "")
        report("ERROR", "import-cycle", comp[0], 0, f"cycle of {len(comp)} files: {shown}")


# --- duplication ------------------------------------------------------------

def normalize(line):
    s = re.sub(r"\s+", " ", line.strip())
    if len(s) < 4 or s in TRIVIAL or s.startswith(("//", "#", "*", "/*", "import ", "from ", "export {", "require(", "package ", "using ")):
        return None
    return s


def check_duplication(files, contents, window):
    seen = {}
    reported = set()
    count = 0
    for rel in files:
        norm = [(i + 1, n) for i, line in enumerate(contents[rel]) if (n := normalize(line))]
        for k in range(len(norm) - window + 1):
            block = "\n".join(n for _, n in norm[k:k + window])
            h = hashlib.sha1(block.encode()).hexdigest()
            here = (rel, norm[k][0])
            if h in seen:
                other = seen[h]
                pair = tuple(sorted((other[0], rel)))
                if pair not in reported and not (other[0] == rel and abs(other[1] - here[1]) < window):
                    reported.add(pair)
                    count += 1
                    if count <= 25:
                        report("WARN", "duplicate-block", rel, here[1], f"{window}+ lines duplicated from {other[0]}:{other[1]}; extract one shared implementation")
            else:
                seen[h] = here
    stats["duplicates"] = count
    if count > 25:
        report("WARN", "duplicate-block", ".", 0, f"{count - 25} more duplicate pairs not shown")


# --- main -------------------------------------------------------------------

def run(root, args):
    findings.clear()
    stats.clear()
    files = walk(root)
    contents = {f: read(root, f) for f in files}
    for f in files:
        check_file(f, contents[f], args)
        check_functions(f, contents[f], args)
    check_dirs(root, files)
    check_imports(root, files, contents)
    check_duplication(files, contents, args.dup_lines)
    return files, contents


def print_report(files, cap=30):
    order = {"ERROR": 0, "WARN": 1}
    shown = {}
    for level, rule, path, line, msg in sorted(findings, key=lambda x: (order[x[0]], x[1], x[2], x[3])):
        shown[rule] = shown.get(rule, 0) + 1
        if shown[rule] <= cap:
            loc = f"{path}:{line}" if line else path
            print(f"{level:5} {rule:24} {loc}  {msg}")
    for rule, n in shown.items():
        if n > cap:
            print(f"      ... {n - cap} more '{rule}' findings")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = len(findings) - errors
    print(f"\nScanned {len(files)} source files: {errors} ERROR, {warns} WARN")
    return errors


def print_stats(files, contents):
    loc = sum(1 for f in files for line in contents[f] if line.strip())
    fns = stats.get("functions", 0)
    print("\nStats")
    print(f"  source files            {len(files)}")
    print(f"  non-blank lines         {loc}")
    print(f"  avg lines per file      {loc // max(len(files), 1)}")
    print(f"  functions               {fns}")
    print(f"  avg function length     {stats.get('function_lines', 0) // max(fns, 1)}")
    print(f"  functions over budget   {stats.get('long_functions', 0)}")
    print(f"  duplicate block pairs   {stats.get('duplicates', 0)}")
    print("  largest files:")
    for f in sorted(files, key=lambda f: -len(contents[f]))[:5]:
        print(f"    {len(contents[f]):6}  {f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--max-lines", type=int, default=500, help="ERROR above this many lines per file")
    p.add_argument("--warn-lines", type=int, default=300, help="WARN above this many lines per file")
    p.add_argument("--dup-lines", type=int, default=8, help="minimum duplicated block size")
    p.add_argument("--max-function", type=int, default=50, help="WARN above this many lines per function")
    p.add_argument("--max-params", type=int, default=4, help="WARN above this many parameters")
    p.add_argument("--max-nesting", type=int, default=3, help="WARN above this block nesting depth (Python)")
    p.add_argument("--stats", action="store_true", help="print size metrics (for before/after comparisons)")
    args = p.parse_args()
    files, contents = run(os.path.abspath(args.root), args)
    errors = print_report(files)
    if args.stats:
        print_stats(files, contents)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
