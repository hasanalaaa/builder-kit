#!/usr/bin/env python3
"""a11y_lint: static accessibility checks for JSX/TSX/HTML/Vue/Svelte/Astro and React Native.

Usage: a11y_lint.py [root]
Static checks catch a fraction of issues: also run axe in E2E plus a keyboard and screen-reader pass.
Each finding: LEVEL rule path:line  message. Exit 1 on any ERROR.
Silence a line with "a11y-lint: ignore"; a file with "a11y-lint: ignore-file".
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

EXT = (".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro", ".mdx")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".turbo", ".expo", "public"}
TEST = re.compile(r"(\.test\.|\.spec\.|__tests__|\.stories\.|e2e/)")

TAG = re.compile(r"<([A-Za-z][\w.]*)((?:\s+(?:[^<>\"'{}]|\"[^\"]*\"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\})*?)?)\s*(/?)>", re.S)
SPREAD = re.compile(r"\{\s*\.\.\.")


def attrs_of(raw):
    return raw or ""


def has(attr_text, *names):
    return any(re.search(rf"(?<![\w-]){re.escape(n)}\s*=", attr_text) for n in names) or bool(SPREAD.search(attr_text))


def walk(root):
    return bk.walk(root, EXT, IGNORE_DIRS)


def element_checks(rel, text, findings):
    labelled_ids = set(re.findall(r"(?:htmlFor|for)\s*=\s*[\"']([\w:-]+)[\"']", text))
    for m in TAG.finditer(text):
        name, a = m.group(1), attrs_of(m.group(2))
        line = text[: m.start()].count("\n") + 1
        if "a11y-lint: ignore" in text.splitlines()[line - 1]:
            continue
        add = lambda level, rule, msg: findings.append((level, rule, rel, line, msg))
        low = name.lower()
        if low == "img" and not has(a, "alt"):
            add("ERROR", "img-alt", "<img> without alt (use alt=\"\" for decorative images)")
        if name in ("Image",) and not has(a, "alt"):
            add("ERROR", "img-alt", "<Image> without alt")
        if low in ("input", "select", "textarea") and not re.search(r"type\s*=\s*[\"'](hidden|submit|button|reset|image)[\"']", a):
            ident = re.search(r"(?<![\w-])id\s*=\s*[\"']([\w:-]+)[\"']", a)
            if not has(a, "aria-label", "aria-labelledby") and not (ident and ident.group(1) in labelled_ids) and not re.search(r"(?<![\w-])id\s*=\s*\{", a):
                before = text[max(0, m.start() - 300): m.start()]
                if not re.search(r"<label\b(?![^>]*>[^<]*</label>)[^>]*>(?:(?!</label>).)*$", before, re.S):
                    add("WARN", "input-label", f"<{name}> without an associated label (label for=id, wrapping label, or aria-label)")
        if low in ("div", "span", "li", "p", "img", "section") and re.search(r"(?<![\w-])on[Cc]lick\s*=", a) and not has(a, "role"):
            add("ERROR", "click-non-interactive", f"onClick on <{name}> without role/keyboard support: use <button> or <a href>")
        if low == "a" and not has(a, "href"):
            add("ERROR", "anchor-no-href", "<a> without href is not keyboard-focusable: use <button> for actions")
        if low == "a" and re.search(r"href\s*=\s*[\"']#[\"']", a):
            add("WARN", "anchor-hash", "href=\"#\" link: use a real URL or a <button>")
        tab = re.search(r"tabIndex\s*=\s*\{?\s*[\"']?([1-9]\d*)", a, re.I)
        if tab:
            add("WARN", "positive-tabindex", "Positive tabindex breaks the natural focus order")
        if re.search(r"(?<![\w-])autoFocus\b|(?<![\w-])autofocus\b", a):
            add("WARN", "autofocus", "autoFocus can disorient screen-reader users; use only in dialogs/search")
        if low == "iframe" and not has(a, "title"):
            add("ERROR", "iframe-title", "<iframe> without title")
        if low in ("button", "a", "input", "select", "textarea") and re.search(r"aria-hidden\s*=\s*[\"{]?\s*[\"']?true", a):
            add("ERROR", "aria-hidden-focusable", f"aria-hidden on focusable <{name}>")
        if low in ("video", "audio") and re.search(r"\bautoPlay\b|\bautoplay\b", a) and not re.search(r"\bmuted\b", a):
            add("WARN", "autoplay-media", "Autoplaying media with sound: mute it and provide controls")
        if low in ("marquee", "blink"):
            add("ERROR", "obsolete-motion", f"<{name}> is inaccessible")
        if low == "html" and not has(a, "lang"):
            add("ERROR", "html-lang", "<html> without lang")
        if name in ("TouchableOpacity", "TouchableHighlight", "Pressable", "TouchableWithoutFeedback") \
                and not has(a, "accessibilityLabel", "accessibilityRole", "aria-label", "role"):
            add("WARN", "rn-touchable-label", f"<{name}> without accessibilityRole/accessibilityLabel")


def icon_button_checks(rel, text, findings):
    for m in re.finditer(r"<button\b([^>]*)>\s*(<(svg|[A-Z]\w*Icon|Icon|[A-Z]\w*)\b[^>]*/?>(?:\s*</\3>)?)\s*</button>", text, re.S):
        a = m.group(1)
        if not has(a, "aria-label", "aria-labelledby", "title"):
            line = text[: m.start()].count("\n") + 1
            if "a11y-lint: ignore" not in text.splitlines()[line - 1]:
                findings.append(("ERROR", "icon-button-name", rel, line, "Icon-only button without aria-label"))


def heading_checks(rel, text, findings):
    levels = [(int(m.group(1)), text[: m.start()].count("\n") + 1) for m in re.finditer(r"<h([1-6])\b", text)]
    for (prev, _), (cur, line) in zip(levels, levels[1:]):
        if cur > prev + 1:
            findings.append(("WARN", "heading-skip", rel, line, f"Heading jumps from h{prev} to h{cur}"))


def run(root):
    findings = []
    for rel in walk(root):
        if TEST.search(rel):
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        if "a11y-lint: ignore-file" in text:
            continue
        element_checks(rel, text, findings)
        icon_button_checks(rel, text, findings)
        heading_checks(rel, text, findings)
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "a11y_lint", note=" (static checks only: also run axe + keyboard + screen reader)")


if __name__ == "__main__":
    sys.exit(main())
