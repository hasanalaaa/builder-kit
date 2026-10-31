#!/usr/bin/env python3
"""rtl_lint: find code that breaks right-to-left layouts or internationalization.

Usage: rtl_lint.py [root] [--strings]
  --strings  also report hard-coded user-facing strings in JSX/TSX/Vue/Svelte even without an i18n library
Each finding: LEVEL rule path:line  message. Exit 1 on any ERROR.
Silence a line with "rtl-lint: ignore" (e.g. a truly physical shadow offset); a file with "rtl-lint: ignore-file".
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

EXT = (".css", ".scss", ".sass", ".less", ".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".astro", ".html", ".dart")
MARKUP = (".tsx", ".jsx", ".vue", ".svelte", ".astro")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".turbo", ".expo", "public", "ios", "android"}
TEST = re.compile(r"(\.test\.|\.spec\.|__tests__|\.stories\.|e2e/|\.d\.ts$)")

CSS_PHYSICAL = re.compile(r"(?<![\w-])(margin-left|margin-right|padding-left|padding-right|border-left|border-right|"
                          r"border-top-left-radius|border-top-right-radius|border-bottom-left-radius|border-bottom-right-radius)\s*:"
                          r"|(?<![\w-])(left|right)\s*:\s*-?\d|text-align\s*:\s*(left|right)\b|float\s*:\s*(left|right)\b")
TW_PHYSICAL = re.compile(r"(?<![\w:-])-?(ml|mr|pl|pr|left|right|border-l|border-r|rounded-l|rounded-r|rounded-tl|rounded-tr|rounded-bl|rounded-br|"
                         r"scroll-ml|scroll-mr|scroll-pl|scroll-pr)-(\[[^\]]+\]|[\w./]+)|(?<![\w:-])(text-left|text-right|float-left|float-right|border-l|border-r|rounded-l|rounded-r)(?![\w-])")
RN_PHYSICAL = re.compile(r"\b(marginLeft|marginRight|paddingLeft|paddingRight|borderLeftWidth|borderRightWidth|borderTopLeftRadius|borderTopRightRadius)\s*:"
                         r"|(?<![\w.])(left|right)\s*:\s*-?\d")
DART_PHYSICAL = re.compile(r"EdgeInsets\.only\([^)]*\b(left|right)\s*:|Alignment\.(centerLeft|centerRight|topLeft|topRight|bottomLeft|bottomRight)\b|Positioned\([^)]*\b(left|right)\s*:")
DIR_ICON = re.compile(r"<(ChevronRight|ChevronLeft|ArrowRight|ArrowLeft|ChevronsRight|ChevronsLeft|CaretRight|CaretLeft|ArrowForward|ArrowBack|ArrowLongRight|ArrowLongLeft)\w*(?![^>]*(rtl:|scale-x|mirror|flip|rotate))[^>]*>")
LOCALELESS = re.compile(r"\.toLocale(Date|Time)?String\(\s*\)|new Intl\.(NumberFormat|DateTimeFormat|RelativeTimeFormat)\(\s*\)|\.toLocaleString\(\s*\)")
JSX_TEXT = re.compile(r">\s*([A-Za-z؀-ۿ][^<>{}]{2,})\s*<")
I18N_LIBS = ("next-intl", "i18next", "react-intl", "vue-i18n", "@nuxtjs/i18n", "@inlang/paraglide", "svelte-i18n", "lingui", "@formatjs/")


def walk(root):
    return bk.walk(root, EXT, IGNORE_DIRS)


def has_i18n(root):
    try:
        with open(os.path.join(root, "package.json"), encoding="utf-8") as f:
            pkg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    return any(any(d.startswith(lib) for lib in I18N_LIBS) for d in deps)


def scan(rel, text, check_strings, findings):
    if "rtl-lint: ignore-file" in text or TEST.search(rel):
        return
    is_css = rel.endswith((".css", ".scss", ".sass", ".less"))
    is_js = rel.endswith((".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".astro", ".html"))
    for n, line in enumerate(text.splitlines(), 1):
        if "rtl-lint: ignore" in line or line.lstrip().startswith(("//", "/*", "*", "#")):
            continue
        add = lambda level, rule, msg: findings.append((level, rule, rel, n, msg))
        if (is_css or rel.endswith((".vue", ".svelte", ".astro", ".html"))) and CSS_PHYSICAL.search(line):
            add("ERROR", "physical-css", "Physical left/right property: use logical (margin-inline-start, inset-inline-end, text-align: start)")
        if is_js and ("class" in line or "cn(" in line or "cva(" in line or "clsx(" in line or "tw`" in line):
            m = TW_PHYSICAL.search(line)
            if m:
                add("ERROR", "physical-tailwind", f"Tailwind physical class '{m.group(0).strip()}': use ms/me/ps/pe/start/end/text-start/rounded-s/border-s")
        if rel.endswith((".tsx", ".jsx", ".ts", ".js")) and RN_PHYSICAL.search(line) and ("style" in text[:4000] or "StyleSheet" in text):
            add("ERROR", "physical-rn-style", "React Native physical style: use marginStart/paddingEnd/start/end")
        if rel.endswith(".dart") and DART_PHYSICAL.search(line):
            add("ERROR", "physical-flutter", "Use EdgeInsetsDirectional / AlignmentDirectional / PositionedDirectional")
        if rel.endswith(MARKUP) and DIR_ICON.search(line):
            add("WARN", "unflipped-icon", "Directional icon without RTL flip: add rtl:-scale-x-100 or a mirrored variant")
        if is_js and LOCALELESS.search(line):
            add("WARN", "localeless-format", "Formatting without an explicit locale: pass the active locale (and numbering system)")
        if check_strings and rel.endswith(MARKUP):
            for m in JSX_TEXT.finditer(line):
                s = m.group(1).strip()
                if len(s) > 2 and not re.fullmatch(r"[\W\d_]+", s) and "{" not in s:
                    add("WARN", "hardcoded-string", f"Hard-coded UI text '{s[:40]}': move to the message catalog")
                    break


def repo_checks(root, files, findings):
    roots = [f for f in files if re.search(r"(^|/)(app/(\[[^\]]+\]/)?layout\.(tsx|jsx)|index\.html|_document\.(tsx|jsx)|app\.html|src/app\.html)$", f)]
    for rel in roots:
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        html = re.search(r"<html\b[^>]*>", text) or re.search(r"<Html\b[^>]*>", text)
        if html and ("lang" not in html.group(0) or "dir" not in html.group(0)):
            findings.append(("ERROR", "html-lang-dir", rel, text[: html.start()].count("\n") + 1, "<html> must set lang and dir from the active locale"))


def run(root, strings=False):
    files = walk(root)
    check_strings = strings or has_i18n(root)
    findings = []
    for rel in files:
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
                scan(rel, f.read(), check_strings, findings)
        except OSError:
            continue
    repo_checks(root, files, findings)
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--strings", action="store_true")
    a = p.parse_args()
    findings = run(a.root, a.strings)
    return bk.report(findings, "rtl_lint")


if __name__ == "__main__":
    sys.exit(main())
