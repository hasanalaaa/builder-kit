#!/usr/bin/env python3
"""Self-test for project_checks with fake tools (no node, go or ruff needed). Run: python3 test_project_checks.py"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project_checks  # noqa: E402


def write(d, rel, body="", exe=False):
    path = os.path.join(d, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(("#!/bin/sh\n" + body) if exe else body)
    if exe:
        os.chmod(path, 0o755)
    return path


def project(files):
    d = tempfile.mkdtemp()
    for rel, body in files.items():
        write(d, rel, body)
    return d


TSC_ERRORS = ("echo \"src/a.ts(3,7): error TS2322: Type 'string' is not assignable to type 'number'.\"\n"
              "echo '  Detail that continues the a.ts error.'\n"
              "echo \"src/old.ts(1,1): error TS2304: Cannot find name 'x'.\"\n"
              "echo '  Detail that continues the old.ts error.'\nexit 2\n")

if __name__ == "__main__":
    fakebin = tempfile.mkdtemp()
    os.environ["PATH"] = fakebin  # hermetic: only the fakes below exist (stubs use absolute /bin/sh)
    run = project_checks.run

    # tsc: errors in a changed file block, errors only in untouched files don't
    d = project({"tsconfig.json": "{}", "src/a.ts": "", "src/b.ts": "", "src/old.ts": "", "src/a.py": ""})
    write(d, "node_modules/.bin/tsc", TSC_ERRORS, exe=True)
    out = run(d, [os.path.join(d, "src/a.ts")], 30)
    text = "\n".join(out)
    assert out and out[0].startswith("[typecheck: tsc --noEmit]"), out
    assert "TS2322" in text and "continues the a.ts" in text and "old.ts" not in text, text
    assert run(d, [os.path.join(d, "src/b.ts")], 30) == [], "pre-existing errors elsewhere must not block"
    assert run(d, [os.path.join(d, "src/a.py")], 30) == [], "no JS change: JS checks don't run"
    assert run(d, [os.path.join(d, "node_modules/.bin/tsc"), "/elsewhere/x.ts"], 30) == []

    # output is capped
    write(d, "node_modules/.bin/tsc", "i=0; while [ $i -lt 40 ]; do echo \"src/a.ts($i,1): error TS1: bad\"; i=$((i+1)); done; exit 2\n", exe=True)
    out = run(d, [os.path.join(d, "src/a.ts")], 30)
    assert len(out) == 1 + 15 + 1 and "25 more" in out[-1], out

    # timeout (a grandchild holds the pipe) skips without blocking, quickly
    write(d, "node_modules/.bin/tsc", "/bin/sleep 30\necho 'src/a.ts(1,1): error TS1: late'\nexit 2\n", exe=True)
    t = time.monotonic()
    assert run(d, [os.path.join(d, "src/a.ts")], 2) == []
    assert time.monotonic() - t < 8, "timeout must kill the process group"

    # budget spent: nothing runs
    marker = os.path.join(d, "ran")
    write(d, "node_modules/.bin/tsc", f"touch {marker}\nexit 2\n", exe=True)
    assert run(d, [os.path.join(d, "src/a.ts")], 0) == [] and not os.path.exists(marker)

    # missing tools skip: tsconfig without node_modules, python and go without any tool installed
    d2 = project({"tsconfig.json": "{}", "src/a.ts": "", "src/mod.py": "", "tests/test_mod.py": "", "pkg/a.go": "", "go.mod": "module m\n"})
    assert run(d2, [os.path.join(d2, p) for p in ("src/a.ts", "src/mod.py", "pkg/a.go")], 30) == []

    # a package.json typecheck script wins over tsc, run with the detected package manager
    d3 = project({"package.json": '{"scripts": {"typecheck": "tsc"}}', "tsconfig.json": "{}", "src/a.ts": "", "pnpm-lock.yaml": ""})
    write(d3, "node_modules/.bin/tsc", "echo 'src/a.ts(1,1): error TS9: from tsc'; exit 2\n", exe=True)
    write(fakebin, "pnpm", "echo \"pnpm $*\"; echo 'src/a.ts(2,2): error TS7: from script'; exit 1\n", exe=True)
    text = "\n".join(run(d3, [os.path.join(d3, "src/a.ts")], 30))
    assert "[typecheck: pnpm run typecheck]" in text and "from script" in text and "from tsc" not in text, text

    # eslint gets the changed JS/TS files only; exit 2 (config error) skips; vitest related shows the tail
    d4 = project({"eslint.config.js": "", "src/a.ts": "", "src/b.ts": "", "src/c.md": ""})
    write(d4, "node_modules/.bin/eslint", "echo \"eslint $*\"; echo '  1:1  error  bad  no-bad'; exit 1\n", exe=True)
    write(d4, "node_modules/.bin/vitest", "echo \"args: $*\"; echo 'FAIL src/a.test.ts > adds'; exit 1\n", exe=True)
    text = "\n".join(run(d4, [os.path.join(d4, p) for p in ("src/a.ts", "src/c.md")], 30))
    assert "[lint: eslint]" in text and "eslint --quiet src/a.ts" in text and "no-bad" in text and "c.md" not in text, text
    assert "[tests: vitest related]" in text and "args: related --run --passWithNoTests src/a.ts" in text and "FAIL" in text, text
    write(d4, "node_modules/.bin/eslint", "echo 'Oops! Something went wrong'; exit 2\n", exe=True)
    assert "eslint" not in "\n".join(run(d4, [os.path.join(d4, "src/a.ts")], 30))

    # python: ruff on the changed files, mypy filtered to them, pytest on the related tests found by name
    d5 = project({"pyproject.toml": "[tool.mypy]\n", "src/mod.py": "", "src/other.py": "", "tests/test_mod.py": "", "README.md": ""})
    write(d5, ".venv/bin/ruff", "echo \"ruff $*\"; exit 1\n", exe=True)
    write(d5, ".venv/bin/mypy", "echo 'src/mod.py:3: error: Incompatible types'; echo 'src/other.py:1: error: old'; exit 1\n", exe=True)
    write(d5, ".venv/bin/pytest", "exit 0\n", exe=True)
    write(d5, ".venv/bin/python", "echo \"python $*\"; echo 'FAILED tests/test_mod.py::test_x - assert 1 == 2'; exit 1\n", exe=True)
    text = "\n".join(run(d5, [os.path.join(d5, p) for p in ("src/mod.py", "README.md")], 30))
    assert "ruff check --quiet --output-format concise src/mod.py" in text, text
    assert "Incompatible types" in text and "src/other.py" not in text, text
    assert "-m pytest -q -p no:cacheprovider tests/test_mod.py" in text and "FAILED" in text, text
    write(d5, ".venv/bin/python", "echo 'no tests ran'; exit 5\n", exe=True)
    assert "pytest" not in "\n".join(run(d5, [os.path.join(d5, "src/mod.py")], 30)), "exit 5 (nothing collected) passes"

    # go: vet filtered to the changed files, go test on the changed packages only
    d6 = project({"go.mod": "module m\n", "pkg/a.go": "", "other/b.go": ""})
    write(fakebin, "go", "if [ \"$1\" = vet ]; then echo '# m/pkg'; echo 'vet: ./pkg/a.go:3:2: unreachable code';"
                        " echo './other/b.go:1:1: old'; exit 1; fi; echo \"--- FAIL: TestA ($*)\"; exit 1\n", exe=True)
    text = "\n".join(run(d6, [os.path.join(d6, "pkg/a.go")], 30))
    assert "[vet: go vet]" in text and "unreachable code" in text and "b.go" not in text, text
    assert "[tests: go test]" in text and "FAIL: TestA (test ./pkg)" in text, text
    print("selftest OK")
