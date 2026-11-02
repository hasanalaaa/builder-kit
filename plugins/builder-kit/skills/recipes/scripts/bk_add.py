#!/usr/bin/env python3
"""bk_add: copy a tested code recipe into a project. Never overwrites a file.

Usage:
  bk_add.py --list
  bk_add.py <recipe> [--dest DIR] [--dry-run]
Exit 0 on success (or dry run), 1 on a conflict (nothing is copied), 2 on a bad recipe name or recipe.json.
A destination that already holds identical content is skipped. An "optional" file (vitest.config.mts) that
already exists is kept as is.
"""
import argparse
import filecmp
import json
import os
import shutil
import sys

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
REQUIRED = ("name", "summary", "files", "deps", "devDeps", "env", "adapt")


class RecipeError(Exception):
    pass


def names():
    return sorted(d for d in os.listdir(ASSETS) if os.path.isfile(os.path.join(ASSETS, d, "recipe.json")))


def load(name):
    """recipe.json with each file's `from` resolved to an absolute path. Raises RecipeError when invalid."""
    if name not in names():
        raise RecipeError(f"unknown recipe '{name}'. Available: {', '.join(names())}")
    folder = os.path.join(ASSETS, name)
    with open(os.path.join(folder, "recipe.json"), encoding="utf-8") as f:
        recipe = json.load(f)
    missing = [k for k in REQUIRED if k not in recipe]
    if missing:
        raise RecipeError(f"{name}/recipe.json: missing {', '.join(missing)}")
    if recipe["name"] != name:
        raise RecipeError(f"{name}/recipe.json: name '{recipe['name']}' != folder")
    for entry in recipe["files"]:
        src = os.path.normpath(os.path.join(folder, entry["from"]))
        if os.path.commonpath([src, ASSETS]) != ASSETS or not os.path.isfile(src):
            raise RecipeError(f"{name}/recipe.json: bad source {entry['from']}")
        to = entry["to"]
        if os.path.isabs(to) or ".." in to.replace("\\", "/").split("/"):
            raise RecipeError(f"{name}/recipe.json: destination must stay inside the project: {to}")
        entry["src"] = src
    return recipe


def plan(recipe, dest):
    """[(entry, target, action)], action: add | same | keep | conflict."""
    out = []
    for entry in recipe["files"]:
        target = os.path.join(dest, entry["to"])
        if not os.path.exists(target):
            action = "add"
        elif os.path.isfile(target) and filecmp.cmp(entry["src"], target, shallow=False):
            action = "same"
        elif entry.get("optional"):
            action = "keep"
        else:
            action = "conflict"
        out.append((entry, target, action))
    return out


def summary(recipe):
    lines = []
    if recipe["deps"]:
        lines.append("Install:      npm i " + " ".join(recipe["deps"]))
    if recipe["devDeps"]:
        lines.append("Install (dev): npm i -D " + " ".join(recipe["devDeps"]))
    for var, why in recipe["env"].items():
        lines.append(f"Env:          {var}  ({why})")
    tests = [e["to"] for e in recipe["files"] if e["to"].endswith((".test.ts", ".test.tsx"))]
    if tests:
        lines.append("Test:         npx vitest run " + " ".join(tests) + "  &&  npx tsc --noEmit")
    lines.append("ADAPT (change these, keep the tested parts):")
    lines += [f"  - {note}" for note in recipe["adapt"]]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Copy a tested code recipe into a project.")
    ap.add_argument("recipe", nargs="?")
    ap.add_argument("--dest", default=".", help="project root (default: current directory)")
    ap.add_argument("--list", action="store_true", help="list recipes")
    ap.add_argument("--dry-run", action="store_true", help="show what would be copied, write nothing")
    args = ap.parse_args(argv)

    if args.list:
        for n in names():
            print(f"{n:18} {load(n)['summary']}")
        return 0
    if not args.recipe:
        ap.print_usage(sys.stderr)
        return 2
    try:
        recipe = load(args.recipe)
    except RecipeError as e:
        print(f"bk_add: {e}", file=sys.stderr)
        return 2

    steps = plan(recipe, args.dest)
    conflicts = [entry["to"] for entry, _, action in steps if action == "conflict"]
    if conflicts:
        for to in conflicts:
            print(f"conflict: {to} already exists with different content", file=sys.stderr)
        print("bk_add: nothing copied. Merge by hand, or add into a scratch --dest and compare.", file=sys.stderr)
        return 1

    label = {"add": "would add" if args.dry_run else "added", "same": "same, skipped", "keep": "exists, kept yours"}
    for entry, target, action in steps:
        if action == "add" and not args.dry_run:
            os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
            with open(entry["src"], "rb") as src, open(target, "xb") as dst:  # x: fail rather than overwrite
                shutil.copyfileobj(src, dst)
        note = "  (make sure it maps @ to ./src)" if action == "keep" else ""
        print(f"{label[action]:15} {entry['to']}{note}")
    print()
    print(summary(recipe))
    return 0


if __name__ == "__main__":
    sys.exit(main())
