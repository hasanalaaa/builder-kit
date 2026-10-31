#!/usr/bin/env python3
"""design_lint: static scan of UI code for craft defects, accessibility bans and generic-AI design patterns.

Usage:
  design_lint.py [root]            # scan CSS/SCSS/TSX/JSX/HTML/Vue/Svelte/Astro under root
  design_lint.py [root] --stats    # also list raw values (colors, font sizes, spacing, radii, z-index) for EXTRACT

Each finding: LEVEL rule path:line  message. Exit 1 on any ERROR.
Silence one line with a comment containing "design-lint: ignore"; a whole file with "design-lint: ignore-file".
Token/theme files (tokens, theme, globals, variables, tailwind.config) may hold raw colors.
"""
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

EXTS = (".css", ".scss", ".sass", ".less", ".tsx", ".jsx", ".ts", ".js", ".html", ".vue", ".svelte", ".astro", ".mdx")
MARKUP = (".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro", ".mdx")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".nuxt", ".svelte-kit", ".output", "out", "coverage",
               "vendor", ".turbo", ".vercel", "public", "storybook-static", "__pycache__", ".venv", "venv"}
TOKEN_FILE = re.compile(r"(tokens?|themes?|globals?|variables|palettes?|colou?rs?)\.(css|scss|ts|js|json)$|tailwind\.config|design-system", re.I)
TEST_FILE = re.compile(bk.TEST_CODE + r"|\.stories\.|fixtures?/")

HEX = r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b"
EMOJI = re.compile("[\U0001F300-\U0001FAFF✨⭐]")

# (level, rule, extensions or None for all, regex, message)
LINE_RULES = [
    ("ERROR", "zoom-disabled", None, re.compile(r"user-scalable\s*=\s*[\"']?(no|0)|maximum-scale\s*=\s*[\"']?1(\.0)?\b"),
     "Zoom disabled: remove user-scalable=no / maximum-scale=1 (WCAG 1.4.4)"),
    ("ERROR", "gradient-text", None, re.compile(r"background-clip\s*:\s*text|-webkit-background-clip\s*:\s*text|\bbg-clip-text\b"),
     "Gradient-filled text is banned (craft-floor §2): emphasize with size/weight/color"),
    ("ERROR", "lorem-ipsum", None, re.compile(r"lorem ipsum", re.I),
     "Placeholder copy in shipped UI: use real content in both languages"),
    ("WARN", "raw-color", None, re.compile(HEX + r"|\brgba?\(\s*\d|\bhsla?\(\s*\d|\b(?:bg|text|border|from|to|via|fill|stroke|ring|shadow)-\[#"),
     "Raw color outside the tokens file: use a semantic token (tokens.md)"),
    ("WARN", "arbitrary-spacing", None, re.compile(r"\b-?(?:p|px|py|pt|pb|pl|pr|ps|pe|m|mx|my|mt|mb|ml|mr|ms|me|gap|gap-x|gap-y|space-x|space-y|top|left|right|bottom|inset|start|end)-\[\d+(?:\.\d+)?px\]"),
     "Arbitrary spacing value: use the spacing scale"),
    ("WARN", "important", None, re.compile(r"!important"), "!important: fix specificity instead (fine inside the reduced-motion reset)"),
    ("WARN", "z-index-chaos", None, re.compile(r"z-index\s*:\s*\d{4,}|\bz-\[\d{3,}\]"), "Huge z-index: use the named z-index scale (tokens.md)"),
    ("WARN", "transition-all", None, re.compile(r"transition\s*:\s*all\b|\btransition-all\b"), "transition: all: list the properties you animate"),
    ("WARN", "layout-animation", None, re.compile(r"transition(?:-property)?\s*:[^;]*\b(width|height|top|left|right|bottom|margin|padding)\b"),
     "Animating layout properties: animate transform/opacity instead (motion.md §4)"),
    ("WARN", "viewport-height", None, re.compile(r"\b100vh\b|\bh-screen\b|\bmin-h-screen\b"), "100vh jumps on mobile: use 100dvh / h-dvh / min-h-dvh"),
    ("WARN", "fixed-width", None, re.compile(r"\bw-\[\d{4,}px\]|(?<![-\w])width\s*:\s*\d{4,}px"), "Fixed width ≥ 1000px: use max-width + fluid width"),
    ("WARN", "glow-shadow", None, re.compile(r"box-shadow\s*:\s*0(px)?\s+0(px)?\s+\d+px\s+\d*p?x?\s*(#|rgba?|hsla?|oklch)|\bshadow-\[0_0_"),
     "Zero-offset colored glow is decoration, not depth: use offset + blur elevation"),
    ("WARN", "accent-border", None, re.compile(r"\bborder-[ls]-(?:4|8|\[\d+px\])\b|border-(?:left|inline-start)\s*:\s*(?:[3-9]|\d{2})px"),
     "Thick colored side border as decoration (craft-floor §3)"),
    ("WARN", "ai-gradient", None, re.compile(r"\bfrom-(?:purple|violet|indigo|fuchsia|pink)-\d{3}\b.*\bto-(?:purple|violet|indigo|fuchsia|pink|blue)-\d{3}\b|linear-gradient\([^)]*(?:#8b5cf6|#a855f7|#6366f1|#7c3aed)[^)]*(?:#ec4899|#6366f1|#3b82f6|#d946ef)", re.I),
     "Default AI purple/indigo/pink gradient: derive color from the brand (color.md §5)"),
]
OUTLINE = re.compile(r"outline\s*:\s*(?:none|0)\b|\boutline-none\b")
FONT_PX = re.compile(r"font-size\s*:\s*(\d+(?:\.\d+)?)px|\btext-\[(\d+(?:\.\d+)?)px\]")
FONT_REM = re.compile(r"font-size\s*:\s*(0?\.\d+)rem|\btext-\[(0?\.\d+)rem\]")
FONT_FAMILY = re.compile(r"font-family\s*:\s*[\"']?([^,;\"'\n]+)")
MOTION = re.compile(r"@keyframes|\banimation\s*:|\banimate-[a-z]|\btransition\b|framer-motion|from\s+[\"']motion|gsap")
REDUCED = re.compile(r"prefers-reduced-motion|motion-reduce:|motion-safe:|useReducedMotion|reducedMotion")


def walk(root):
    return bk.walk(root, EXTS, IGNORE_DIRS)


def scan_file(rel, text, findings, stats):
    if "design-lint: ignore-file" in text:
        return
    is_token = bool(TOKEN_FILE.search(rel))
    is_test = bool(TEST_FILE.search(rel))
    has_focus_visible = "focus-visible" in text or "focus:ring" in text or ":focus" in text
    is_markup = rel.endswith(MARKUP)
    for n, line in enumerate(text.splitlines(), 1):
        if "design-lint: ignore" in line:
            continue
        for level, rule, exts, rx, msg in LINE_RULES:
            if exts and not rel.endswith(exts):
                continue
            if rule == "raw-color" and (is_token or is_test):
                continue
            if rule == "lorem-ipsum" and is_test:
                continue
            if rx.search(line):
                findings.append((level, rule, rel, n, msg))
        if OUTLINE.search(line):
            same_line = re.search(r"focus-visible|focus:ring|ring-|box-shadow", line)
            if not same_line:
                findings.append(("WARN" if has_focus_visible else "ERROR", "focus-removed", rel, n,
                                 "Focus outline removed: add a visible :focus-visible style (WCAG 2.4.7)"))
        for m in FONT_PX.finditer(line):
            v = float(m.group(1) or m.group(2))
            stats["font-size"][f"{v:g}px"] += 1
            if v < 12:
                findings.append(("ERROR", "tiny-text", rel, n, f"Font size {v:g}px < 12px floor"))
        for m in FONT_REM.finditer(line):
            v = float(m.group(1) or m.group(2))
            stats["font-size"][f"{v:g}rem"] += 1
            if v < 0.75:
                findings.append(("ERROR", "tiny-text", rel, n, f"Font size {v:g}rem < 0.75rem floor"))
        if is_markup and not is_test and EMOJI.search(line) and not line.lstrip().startswith(("//", "/*", "*", "{/*")):
            findings.append(("WARN", "emoji-icon", rel, n, "Emoji in UI markup: use the icon library (components.md §14)"))
        for m in re.finditer(HEX, line):
            stats["color"][m.group(0).lower()] += 1
        for m in re.finditer(r"(?:padding|margin|gap)[\w-]*\s*:\s*([^;]+)", line):
            for px in re.findall(r"(\d+(?:\.\d+)?)px", m.group(1)):
                stats["spacing"][px + "px"] += 1
                if float(px) > 2 and float(px) % 4:
                    findings.append(("WARN", "off-scale-spacing", rel, n, f"Spacing {px}px is off the 4px scale"))
        for m in re.finditer(r"border-radius\s*:\s*([^;]+)|\brounded-\[([^\]]+)\]", line):
            stats["radius"][(m.group(1) or m.group(2)).strip()] += 1
        for m in re.finditer(r"z-index\s*:\s*(-?\d+)|\bz-\[?(\d+)\]?", line):
            stats["z-index"][m.group(1) or m.group(2)] += 1
        for m in FONT_FAMILY.finditer(line):
            name = m.group(1).strip()
            if not name.startswith("var(") and name.lower() not in ("inherit", "initial", "unset"):
                stats["font-family"][name] += 1


def repo_checks(texts, findings, stats):
    families = [f for f in stats["font-family"] if f.lower() not in ("system-ui", "sans-serif", "serif", "monospace", "-apple-system")]
    if len(families) > 4:
        findings.append(("WARN", "too-many-fonts", ".", 0, f"{len(families)} font families declared: {', '.join(sorted(families)[:8])} (≤ 3 + Arabic pair)"))
    all_text = "\n".join(texts.values())
    if MOTION.search(all_text) and not REDUCED.search(all_text):
        findings.append(("WARN", "no-reduced-motion", ".", 0, "Motion found but no prefers-reduced-motion handling anywhere (motion.md §5)"))


def print_report(findings, cap=30):
    by_rule = collections.defaultdict(list)
    for f in findings:
        by_rule[(f[0], f[1])].append(f)
    for (level, rule), items in sorted(by_rule.items(), key=lambda kv: (kv[0][0] != "ERROR", kv[0][1])):
        for lv, r, path, line, msg in items[:cap]:
            loc = f"{path}:{line}" if line else path
            print(f"{lv:5} {r:18} {loc}  {msg}")
        if len(items) > cap:
            print(f"{level:5} {rule:18} … {len(items) - cap} more")
    errors = sum(f[0] == "ERROR" for f in findings)
    print(f"\ndesign_lint: {errors} ERROR, {len(findings) - errors} WARN")
    return errors


def print_stats(stats):
    print("\n## Raw values in use (cluster these into tokens)")
    for key in ("color", "font-size", "spacing", "radius", "z-index", "font-family"):
        items = stats[key].most_common(25)
        print(f"- {key} ({len(stats[key])} distinct): " + ", ".join(f"{k}×{v}" for k, v in items))


def run(root):
    findings, stats, texts = [], collections.defaultdict(collections.Counter), {}
    for rel in walk(root):
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
                texts[rel] = f.read()
        except OSError:
            continue
        scan_file(rel, texts[rel], findings, stats)
    repo_checks(texts, findings, stats)
    return findings, stats


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--stats", action="store_true", help="print raw value inventory")
    a = p.parse_args()
    findings, stats = run(a.root)
    return bk.report(findings, "design_lint", a.root)


if __name__ == "__main__":
    sys.exit(main())
