#!/usr/bin/env python3
"""Plugin integrity: every skill, command, agent, script, reference and gate registration is consistent.
Run: python3 test_integrity.py"""
import glob
import json
import os
import re
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN, "skills", "ship", "scripts"))
import ship_check  # noqa: E402

FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def front(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = FRONT.match(text)
    assert m, f"{path}: missing frontmatter"
    fields = dict(re.findall(r"^([\w-]+):\s*(.*)$", m.group(1), re.M))
    return fields, text


def rel(p):
    return os.path.relpath(p, PLUGIN)


if __name__ == "__main__":
    problems = []
    skills = sorted(d for d in os.listdir(os.path.join(PLUGIN, "skills")) if not d.startswith("."))
    commands = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(PLUGIN, "commands", "*.md"))}
    agents = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(PLUGIN, "agents", "*.md"))}
    docs = []
    for s in skills:
        path = os.path.join(PLUGIN, "skills", s, "SKILL.md")
        if not os.path.exists(path):
            problems.append(f"skills/{s}: no SKILL.md")
            continue
        fields, text = front(path)
        if fields.get("name") != s:
            problems.append(f"{rel(path)}: name '{fields.get('name')}' != folder '{s}'")
        desc = fields.get("description", "")
        if not 80 <= len(desc) <= 1024:
            problems.append(f"{rel(path)}: description is {len(desc)} chars (want 80-1024)")
        docs.append((path, s, text))
        for ref in glob.glob(os.path.join(PLUGIN, "skills", s, "references", "*.md")):
            with open(ref, encoding="utf-8") as f:
                docs.append((ref, s, f.read()))
    for kind, names in (("commands", commands), ("agents", agents)):
        for n in names:
            path = os.path.join(PLUGIN, kind, n + ".md")
            fields, text = front(path)
            if not fields.get("description"):
                problems.append(f"{rel(path)}: no description")
            if kind == "agents" and fields.get("name") != n:
                problems.append(f"{rel(path)}: name '{fields.get('name')}' != file '{n}'")
            docs.append((path, None, text))
    for path, skill, text in docs:
        for m in re.finditer(r"builder-kit:([a-z0-9-]+)", text):
            if m.group(1) not in set(skills) | commands | agents:
                problems.append(f"{rel(path)}: unknown {m.group(0)}")
        for m in re.finditer(r"(?<![\w/.-])((?:[\w-]+/)?(?:references|scripts|data)/[\w.-]+\.(?:md|py|sh|csv|json))", text):
            ref = m.group(1)
            here = [os.path.join(PLUGIN, "skills", skill, ref)] if skill else []
            if not any(os.path.exists(c) for c in here + [os.path.join(PLUGIN, "skills", ref)]
                       + [os.path.join(PLUGIN, "skills", x, ref) for x in skills]):
                problems.append(f"{rel(path)}: missing {ref}")
    for script in glob.glob(os.path.join(PLUGIN, "skills", "*", "scripts", "*.py")):
        name = os.path.basename(script)
        if not name.startswith("test_") and not glob.glob(os.path.join(os.path.dirname(script), "test_*.py")):
            problems.append(f"{rel(script)}: no test_*.py beside it")
    facts = {"seo_dir": None, "data": True, "frontend": True, "design": True, "a11y": True, "rtl": True, "legal": True,
             "ai": True, "mobile": True, "perf": True}
    with open(os.path.join(PLUGIN, "skills", "ship", "references", "lifecycle.md"), encoding="utf-8") as f:
        lifecycle = f.read()
    for key, _, script, _, _ in ship_check.scanners("/x", facts):
        if not os.path.exists(os.path.join(PLUGIN, "skills", script)):
            problems.append(f"ship_check: {key} → missing {script}")
        if f"| {key} | `{script}`" not in lifecycle:
            problems.append(f"lifecycle.md: scanner '{key}' ({script}) not in the scanner table")
    with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        problems.append("plugin.json: version is not semver")
    if f"{len(skills)} skills" not in manifest.get("description", ""):
        problems.append(f"plugin.json: description should say '{len(skills)} skills'")
    assert not problems, "\n".join(problems)
    print("selftest OK")
