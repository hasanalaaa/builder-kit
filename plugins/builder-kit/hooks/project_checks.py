#!/usr/bin/env python3
"""The project's own checks for the Stop gate: typecheck, lint and related tests on the files changed this session.

Only locally installed tools run (node_modules/.bin, .venv, PATH); nothing is downloaded. Typecheck and lint output
is filtered to the changed files, so pre-existing errors in untouched files never block. A missing tool, a crash,
a timeout or an exhausted budget skips that check without blocking. Passing checks print nothing.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import time

from post_edit import SKIP_PARTS

JS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
PER_CHECK = 60  # seconds; the overall budget caps it further
MAX_LINES = 15
MAX_WIDTH = 300
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
ESLINT_CONFIGS = ("eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts", "eslint.config.mts",
                  "eslint.config.cts", ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yml",
                  ".eslintrc.yaml")
MAX_WALK_DIRS = 5000


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""  # missing file: treated as empty


def _local(root, rel):
    path = os.path.join(root, rel)
    return path if os.path.isfile(path) and os.access(path, os.X_OK) else None


def _relevant(root, paths):
    """Changed files under root, relative to it, minus dependency/build folders."""
    rels = []
    for p in paths:
        p = os.path.abspath(p)
        if not p.startswith(root + os.sep) or not os.path.isfile(p):
            continue
        rel = os.path.relpath(p, root)
        if not set(rel.split(os.sep)) & SKIP_PARTS:
            rels.append(rel)
    return rels


def _related_py_tests(root, py):
    direct = [r for r in py if os.path.basename(r).startswith("test_") or r.endswith("_test.py")]
    names = set()
    for r in py:
        mod = os.path.basename(r)[:-3]
        if r not in direct and mod != "__init__":
            names |= {f"test_{mod}.py", f"{mod}_test.py"}
    found, seen = [], 0
    for d, dirs, files in os.walk(root):
        seen += 1
        if seen > MAX_WALK_DIRS:
            break  # ponytail: bounded walk; huge repos may miss far-away tests, use a real test map if that matters
        dirs[:] = sorted(x for x in dirs if x not in SKIP_PARTS and not x.startswith("."))
        found += [os.path.relpath(os.path.join(d, f), root) for f in sorted(files) if f in names]
    return list(dict.fromkeys(direct + found))


def _package_manager(root):
    # same lockfile order as ship_check.run_tests
    return next((pm for lock, pm in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun"))
                 if os.path.exists(os.path.join(root, lock))), "npm")


# Each check: (label, cmd, run_cwd, fail_codes | None for any non-zero, files to filter output on | None, show tail).

def _js_checks(root, js):
    try:
        pkg = json.loads(_read(os.path.join(root, "package.json")) or "{}")
    except ValueError:
        pkg = {}  # broken package.json: no scripts to run
    scripts = pkg.get("scripts") or {}
    script = next((s for s in ("typecheck", "type-check") if scripts.get(s)), None)
    tsc = _local(root, "node_modules/.bin/tsc")
    if script:
        pm = _package_manager(root)
        yield f"typecheck: {pm} run {script}", [pm, "run", script], root, None, js, False
    elif tsc and os.path.exists(os.path.join(root, "tsconfig.json")):
        yield "typecheck: tsc --noEmit", [tsc, "--noEmit", "--pretty", "false"], root, None, js, False
    eslint = _local(root, "node_modules/.bin/eslint")
    if eslint and (any(os.path.exists(os.path.join(root, c)) for c in ESLINT_CONFIGS) or "eslintConfig" in pkg):
        yield "lint: eslint", [eslint, "--quiet", *js], root, {1}, None, False  # 2 = config/crash: skip
    vitest, jest = _local(root, "node_modules/.bin/vitest"), _local(root, "node_modules/.bin/jest")
    if vitest:
        yield "tests: vitest related", [vitest, "related", "--run", "--passWithNoTests", *js], root, {1}, None, True
    elif jest:
        yield "tests: jest --findRelatedTests", [jest, "--ci", "--passWithNoTests", "--findRelatedTests", *js], root, {1}, None, True


def _py_checks(root, py):
    exists = lambda name: os.path.exists(os.path.join(root, name))  # noqa: E731
    venv = next((d for d in (".venv", "venv") if os.path.isdir(os.path.join(root, d, "bin"))), None)
    tool = lambda name: (venv and _local(root, f"{venv}/bin/{name}")) or shutil.which(name)  # noqa: E731
    ruff = tool("ruff")
    if ruff:
        yield "lint: ruff check", [ruff, "check", "--quiet", "--output-format", "concise", *py], root, {1}, None, False
    cfg = _read(os.path.join(root, "pyproject.toml")) + _read(os.path.join(root, "setup.cfg"))
    mypy = tool("mypy")
    if mypy and ("[tool.mypy]" in cfg or "[mypy]" in cfg or exists("mypy.ini") or exists(".mypy.ini")):
        yield "typecheck: mypy", [mypy, *py], root, None, py, False
    pyright = tool("pyright") or _local(root, "node_modules/.bin/pyright")
    if pyright and ("[tool.pyright]" in cfg or exists("pyrightconfig.json")):
        yield "typecheck: pyright", [pyright, *py], root, None, py, False
    tests = _related_py_tests(root, py)
    if venv and _local(root, f"{venv}/bin/pytest"):
        pytest = [os.path.join(root, venv, "bin", "python"), "-m", "pytest"]
    else:
        pytest = [shutil.which("pytest")] if shutil.which("pytest") else None
    if tests and pytest:  # 1 = failures, 2 = collection errors; 5 = nothing collected: pass
        yield "tests: pytest", [*pytest, "-q", "-p", "no:cacheprovider", *tests], root, {1, 2}, None, True


def _go_checks(root, go_files):
    go = shutil.which("go")
    if not go:
        return
    modules = {}
    for r in go_files:  # group by the nearest go.mod at or below root
        d = os.path.dirname(os.path.join(root, r))
        while not os.path.exists(os.path.join(d, "go.mod")) and d != root:
            d = os.path.dirname(d)
        if os.path.exists(os.path.join(d, "go.mod")):
            modules.setdefault(d, []).append(os.path.relpath(os.path.join(root, r), d))
    for mod, files in modules.items():
        pkgs = sorted({"./" + os.path.dirname(f) if os.path.dirname(f) else "." for f in files})
        yield "vet: go vet", [go, "vet", *pkgs], mod, None, files, False
        yield "tests: go test", [go, "test", *pkgs], mod, {1}, None, True


def checks(root, rels):
    js = [r for r in rels if r.endswith(JS)]
    py = [r for r in rels if r.endswith(".py")]
    go_files = [r for r in rels if r.endswith(".go")]
    if js:
        yield from _js_checks(root, js)
    if py:
        yield from _py_checks(root, py)
    if go_files:
        yield from _go_checks(root, go_files)


def _exec(cmd, cwd, timeout):
    """(returncode, output without ANSI), or None when the tool is missing or timed out."""
    env = {**os.environ, "CI": "1", "NO_COLOR": "1", "FORCE_COLOR": "0"}
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, errors="replace", env=env, start_new_session=True)
    except OSError:
        return None  # tool missing or not executable: skip the check
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:  # kill the whole group: `npm run` leaves grandchildren holding the pipe otherwise
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass  # already gone, or a grandchild left the group: abandon it, the check is skipped either way
        return None
    return p.returncode, ANSI.sub("", out)


def _mentioning(lines, run_cwd, files):
    """Lines naming one of files (relative to run_cwd or absolute), plus the deeper-indented lines that continue them."""
    names = set()
    for f in files:
        full = os.path.join(run_cwd, f)
        names |= {f, full, os.path.realpath(full)}
    pat = re.compile(r"(?<![\w./-])(?:\./)?(?:" + "|".join(map(re.escape, sorted(names, key=len, reverse=True))) + r")(?=[:(\s,]|$)")
    kept, depth = [], None
    for line in lines:
        indent = len(line) - len(line.lstrip())
        if pat.search(line):
            kept.append(line)
            depth = indent
        elif depth is not None and line.strip() and indent > depth:
            kept.append(line)
        else:
            depth = None
    return kept


def run(cwd, changed_paths, budget_seconds=90):
    """Report lines for the project checks failing on changed_paths; empty when all pass or none apply."""
    deadline = time.monotonic() + budget_seconds
    root = os.path.abspath(cwd)
    report = []
    for label, cmd, run_cwd, fail, files, tail in checks(root, _relevant(root, changed_paths)):
        left = deadline - time.monotonic()
        if left < 1:
            break  # budget spent: the remaining checks are skipped, never blocking
        result = _exec(cmd, run_cwd, min(PER_CHECK, left))
        if result is None or result[0] == 0 or (fail and result[0] not in fail):
            continue
        lines = [ln.rstrip() for ln in result[1].splitlines()]
        if files is not None:
            lines = _mentioning(lines, run_cwd, files)
            if not lines:
                continue  # failures only in files this session did not touch
        lines = [ln[:MAX_WIDTH] for ln in lines if ln.strip()]
        shown = lines[-MAX_LINES:] if tail else lines[:MAX_LINES]
        more = [f"  … {len(lines) - len(shown)} more line(s)"] if len(lines) > len(shown) else []
        body = [f"  {ln}" for ln in shown]
        report += [f"[{label}] fails on what you changed:"] + (more + body if tail else body + more)
    return report
