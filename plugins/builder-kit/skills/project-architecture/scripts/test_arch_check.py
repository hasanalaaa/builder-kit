#!/usr/bin/env python3
"""Tests for arch_check.py: a messy tree must trigger every rule, a clean tree must stay silent.

Run: python3 test_arch_check.py
"""
import argparse  # noqa: F401  (used by some fixtures)
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arch_check import findings, run  # noqa: E402


def main():
    args = argparse.Namespace(max_lines=500, warn_lines=300, dup_lines=8, max_function=50, max_params=4, max_nesting=3)
    long_py = "def long_fn():\n" + "    x = 1\n" * 55
    deep_py = ("def deep(a, b, c, d, e):\n    for i in a:\n        if i:\n            while b:\n"
               "                with c:\n                    return d\n")
    elif_py = "def chain(x):\n    if x == 1:\n        return 1\n    elif x == 2:\n        return 2\n    elif x == 3:\n        return 3\n    else:\n        return 0\n"
    long_js = "export function render(a, b, c, d, e) {\n" + "  const v = a + 1;\n" * 55 + "}\n"
    dup = "\n".join(f"const value{i} = compute(input, {i}) + offset;" for i in range(10)) + "\n"
    tree = {
        "src/features/a/index.ts": "export * from './x';\n",
        "src/features/a/x.ts": "import { y } from '../b/internal';\nimport { z } from './z';\nexport const x = 1;\n",
        "src/features/a/z.ts": "import { x } from './x';\nexport const z = 2;\n",
        "src/features/b/index.ts": "export * from './internal';\n",
        "src/features/b/internal.ts": "export const y = 3;\n",
        "src/shared/money.ts": "import { x } from '@/features/a';\nexport const m = x;\n",
        "src/big.ts": "const a = 1;\n" * 520,
        "src/helpers_v2.ts": "export const h = 1;\n",
        "src/dead.ts": "".join(f"// const old{i} = call({i});\n" for i in range(6)) + "export const d = 1;\n",
        "src/d1.ts": dup,
        "src/d2.ts": dup,
        "app/__init__.py": "",
        "app/m1.py": "from . import m2\n",
        "app/m2.py": "from .m1 import f\n",
        "app/long.py": long_py + deep_py,
        "src/view.ts": long_js,
    }
    clean = {
        "src/features/a/index.ts": "export { x } from './x';\n",
        "src/features/a/x.ts": "import { y } from '../b';\nexport const x = y + 1;\n",
        "src/features/b/index.ts": "export const y = 3;\n",
        "src/shared/money.ts": "export const toCents = (n: number) => Math.round(n * 100);\n",
        "src/notes.ts": "//   npm run mock      seeded vault (passphrase below)\n" * 3
                        + "//   MOCK_USB=0         start in the not plugged in state\n" * 3 + "export const n = 1;\n",
        "third_party/lib/a.ts": dup,
        "third_party/lib/b.ts": dup,
        "src/chain.py": elif_py,
        "src/short.ts": "export const add = (a: number, b: number) => {\n  return a + b;\n};\n",
    }
    for name, spec in (("messy", tree), ("clean", clean)):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in spec.items():
                path = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)
            run(tmp, args)
            rules = {(f[1], f[2]) for f in findings}
            if name == "messy":
                expected = {
                    ("feature-internal-import", "src/features/a/x.ts"),
                    ("shared-imports-feature", "src/shared/money.ts"),
                    ("file-too-long", "src/big.ts"),
                    ("versioned-copy", "src/helpers_v2.ts"),
                    ("commented-out-code", "src/dead.ts"),
                    ("duplicate-block", "src/d2.ts"),
                    ("function-too-long", "app/long.py"),
                    ("too-many-params", "app/long.py"),
                    ("deep-code-nesting", "app/long.py"),
                    ("function-too-long", "src/view.ts"),
                    ("too-many-params", "src/view.ts"),
                }
                missing = expected - rules
                assert not missing, f"selftest missed: {missing}"
                cycles = [f for f in findings if f[1] == "import-cycle"]
                assert len(cycles) == 2, f"expected 2 cycles (TS + Python), got {cycles}"
            else:
                assert not findings, f"clean tree should have no findings, got {findings}"
    print("selftest OK")


if __name__ == "__main__":
    main()
