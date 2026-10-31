#!/usr/bin/env python3
"""perf_budget: check build output and source assets against performance budgets.

Usage:
  perf_budget.py [root] [--build-dir DIR] [--js-budget KB] [--css-budget KB] [--chunk-budget KB] [--image-kb KB] [--font-kb KB]
Build dir auto-detected: .next/static, dist, build, out, .output/public, .svelte-kit/output/client.
Sizes for JS/CSS budgets are gzip sizes in KB. Exit 1 when a budget is exceeded (ERROR).
"""
import argparse
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

BUILD_DIRS = [".next/static", "dist", "build", "out", ".output/public", ".svelte-kit/output/client"]
IGNORE_DIRS = {"node_modules", ".git", ".next", "dist", "build", "out", ".output", "coverage", ".turbo", ".expo", "ios", "android", "Pods"}
IMG = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".tiff")
FONT = (".woff", ".woff2", ".ttf", ".otf", ".eot")
HEAVY = {
    "moment": "use date-fns, dayjs or Intl (moment is large and not tree-shakable)",
    "lodash": "import per-function from lodash-es or use native methods",
    "jquery": "not needed in a React/Vue/Svelte app",
    "aws-sdk": "v2 SDK is huge: use modular @aws-sdk/client-* (v3), server-side only",
    "firebase": "import modular subpaths only (firebase/auth, firebase/firestore)",
    "@mui/icons-material": "import icons by path, never the barrel",
    "core-js": "target modern browsers; avoid blanket polyfills",
    "rxjs": "check it is really needed on the client",
    "three": "lazy-load 3D scenes on visibility",
    "chart.js": "lazy-load charts; consider lighter options",
    "highlight.js": "load only needed languages; or render on the server",
    "pdfjs-dist": "lazy-load PDF viewer",
    "xlsx": "lazy-load or move spreadsheet parsing to the server",
}
UI_KITS = ["@mui/material", "antd", "@chakra-ui/react", "@mantine/core", "react-bootstrap", "bootstrap", "semantic-ui-react", "primereact"]
CHART_LIBS = ["recharts", "chart.js", "react-chartjs-2", "echarts", "highcharts", "victory", "@nivo/core", "apexcharts", "d3", "plotly.js"]


def gz_size(path):
    with open(path, "rb") as f:
        return len(gzip.compress(f.read(), 9))


def find_build(root, explicit):
    if explicit:
        p = os.path.join(root, explicit)
        return p if os.path.isdir(p) else None
    for d in BUILD_DIRS:
        p = os.path.join(root, d)
        if os.path.isdir(p):
            return p
    return None


def build_checks(build, a, findings, report):
    js, css = [], []
    for d, _, files in os.walk(build):
        for f in files:
            p = os.path.join(d, f)
            if f.endswith((".js", ".mjs")) and not f.endswith(".map"):
                js.append((gz_size(p), os.path.getsize(p), os.path.relpath(p, a.root)))
            elif f.endswith(".css"):
                css.append((gz_size(p), os.path.getsize(p), os.path.relpath(p, a.root)))
    js_total, css_total = sum(x[0] for x in js) / 1024, sum(x[0] for x in css) / 1024
    report.append(f"Build: {build}")
    report.append(f"  JS  {len(js)} files · {js_total:.0f} KB gzip total (all routes)")
    report.append(f"  CSS {len(css)} files · {css_total:.0f} KB gzip total")
    for g, raw, rel in sorted(js, reverse=True)[:8]:
        report.append(f"    {g / 1024:7.1f} KB gz ({raw / 1024:.0f} KB raw)  {rel}")
    if js_total > a.js_budget:
        findings.append(("ERROR", "js-budget", f"Total JS {js_total:.0f} KB gzip > budget {a.js_budget} KB (split routes, lazy-load heavy widgets, server components)"))
    if css_total > a.css_budget:
        findings.append(("ERROR", "css-budget", f"Total CSS {css_total:.0f} KB gzip > budget {a.css_budget} KB"))
    for g, raw, rel in js:
        if g / 1024 > a.chunk_budget:
            findings.append(("WARN", "large-chunk", rel, f"{rel} is {g / 1024:.0f} KB gzip (> {a.chunk_budget} KB): find what it bundles (bundle analyzer)"))
    for g, raw, rel in js + css:
        if raw > 0 and g / raw > 0.9 and raw > 50_000:
            findings.append(("WARN", "uncompressed-like", rel, f"{rel} barely compresses: is it already minified binary/data inlined in JS?"))


def dependency_checks(root, findings):
    try:
        with open(os.path.join(root, "package.json"), encoding="utf-8") as f:
            pkg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    deps = pkg.get("dependencies", {})
    for name, why in HEAVY.items():
        if name in deps:
            findings.append(("WARN", "heavy-dependency", f"{name}: {why}"))
    kits = [k for k in UI_KITS if k in deps]
    if len(kits) > 1:
        findings.append(("WARN", "duplicate-ui-kits", f"Several UI kits shipped: {', '.join(kits)}"))
    charts = [c for c in CHART_LIBS if c in deps]
    if len(charts) > 1:
        findings.append(("WARN", "duplicate-chart-libs", f"Several chart libraries: {', '.join(charts)}"))


def asset_checks(root, a, findings):
    fonts = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in IGNORE_DIRS and not x.startswith(".")]
        for f in files:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root)
            size = os.path.getsize(p) / 1024
            low = f.lower()
            if low.endswith(IMG) and size > a.image_kb:
                fmt = "" if low.endswith((".webp", ".avif")) else " and convert to AVIF/WebP"
                findings.append(("WARN", "large-image", rel, f"{rel} is {size:.0f} KB: resize{fmt}, or serve via an image CDN"))
            if low.endswith(FONT):
                fonts.append((rel, size))
                if not low.endswith(".woff2"):
                    findings.append(("WARN", "font-format", rel, f"{rel}: ship WOFF2 only"))
                if size > a.font_kb:
                    findings.append(("WARN", "large-font", rel, f"{rel} is {size:.0f} KB: subset to used scripts/weights"))
    if len(fonts) > 6:
        findings.append(("WARN", "many-fonts", f"{len(fonts)} font files in the repo: keep ≤ 4 on first load"))


def run(root, a):
    findings, report = [], []
    build = find_build(root, a.build_dir)
    if build:
        build_checks(build, a, findings, report)
    else:
        report.append("No build output found: run the build first (or pass --build-dir) to check JS/CSS budgets")
    dependency_checks(root, findings)
    asset_checks(root, a, findings)
    return findings, report


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--build-dir")
    p.add_argument("--js-budget", type=float, default=350, help="total JS gzip KB across the build (default 350)")
    p.add_argument("--css-budget", type=float, default=60)
    p.add_argument("--chunk-budget", type=float, default=150, help="single JS chunk gzip KB (default 150)")
    p.add_argument("--image-kb", type=float, default=300)
    p.add_argument("--font-kb", type=float, default=120)
    return p


def main():
    a = parser().parse_args()
    findings, report = run(a.root, a)
    print("\n".join(report))
    return bk.report(findings, "perf_budget", a.root)


if __name__ == "__main__":
    sys.exit(main())
