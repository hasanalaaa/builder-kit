#!/usr/bin/env python3
"""Self-test for the design-system tools. Run: python3 test_design_tools.py"""
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import contrast  # noqa: E402
import design_lint  # noqa: E402
import design_search  # noqa: E402
import palette  # noqa: E402


def test_contrast():
    assert round(contrast.wcag_ratio((0, 0, 0), (255, 255, 255)), 2) == 21.0
    assert abs(contrast.apca((0, 0, 0), (255, 255, 255)) - 106.04) < 0.2
    assert abs(contrast.apca((255, 255, 255), (0, 0, 0)) + 107.88) < 0.2
    assert contrast.parse_color("#fff") == (255, 255, 255)
    assert contrast.parse_color("222.2 84% 4.9%") is not None
    for hexv in ("#2563eb", "#f59e0b", "#006c35", "#18181b"):
        rgb = contrast.parse_color(hexv)
        back = contrast.oklch_to_rgb(*contrast.rgb_to_oklch(rgb))
        assert max(abs(a - b) for a, b in zip(rgb, back)) <= 1, hexv
    assert contrast.parse_color("oklch(0.5 0.1 250)") is not None


def test_palette_all_seeds_pass():
    with open(os.path.join(HERE, "..", "data", "palettes.csv"), encoding="utf-8") as f:
        seeds = [r["brand_hex"] for r in csv.DictReader(f)]
    for hexv in seeds:
        L, C, H = contrast.rgb_to_oklch(contrast.parse_color(hexv))
        p = palette.build(H, max(C, 0.04), brand=(L, C, H))
        for fmt in ("css", "tailwind", "shadcn"):
            results = contrast.check_tokens(palette.render(p, fmt, "t"))
            bad = [r for r in results if r[4] and not r[5]]
            assert results and not bad, (hexv, fmt, bad[:3])


def test_lint_messy_and_clean():
    messy = {
        "app/page.tsx": ('<meta name="viewport" content="width=device-width, maximum-scale=1">\n'
                         '<h1 className="bg-clip-text text-transparent from-purple-500 to-pink-500 text-[10px]">🚀 Lorem ipsum</h1>\n'
                         '<div className="outline-none p-[13px] z-[9999] h-screen transition-all border-l-4 bg-[#ff00ff] w-[1440px]"/>\n'),
        "app/a.css": ".x{color:#123456;padding:13px;transition: width .2s;box-shadow: 0 0 20px #f0f;z-index: 99999}\n@keyframes k{}\n",
    }
    clean = {
        "app/page.tsx": '<h1 className="text-4xl font-semibold text-foreground">Invoices</h1>\n'
                        '<button className="focus-visible:ring-2 px-4 py-2 min-h-dvh">Create invoice</button>\n',
        "styles/tokens.css": ":root{--color-primary:#2563eb}\n@media (prefers-reduced-motion: reduce){*{transition:none}}\n",
    }
    expected = {"zoom-disabled", "gradient-text", "lorem-ipsum", "raw-color", "arbitrary-spacing", "z-index-chaos",
                "transition-all", "layout-animation", "viewport-height", "fixed-width", "glow-shadow", "accent-border",
                "ai-gradient", "focus-removed", "tiny-text", "emoji-icon", "off-scale-spacing", "no-reduced-motion"}
    for files, want in ((messy, expected), (clean, set())):
        with tempfile.TemporaryDirectory() as d:
            for rel, body in files.items():
                os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
                with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                    f.write(body)
            findings, _ = design_lint.run(d)
            got = {f[1] for f in findings}
            assert want <= got if want else not got, (sorted(want - got), sorted(got))


def test_database_integrity():
    ids = {}
    for domain in design_search.DOMAINS:
        path = os.path.join(HERE, "..", "data", f"{domain}.csv")
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        assert all(len(r) == len(header) for r in rows), (domain, [r[0] for r in rows if len(r) != len(header)])
        ids[domain] = {r[0] for r in rows}
        assert len(ids[domain]) == len(rows), f"duplicate id in {domain}"
    for p in design_search.load("products"):
        for key, domain in (("styles", "styles"), ("palettes", "palettes"), ("fonts", "fonts")):
            missing = [i for i in p[key].split(";") if i not in ids[domain]]
            assert not missing, (p["id"], key, missing)
        assert not p["landing"] or p["landing"] in ids["landing"], p["id"]


def test_recommend():
    assert "restaurant" in design_search.recommend("موقع مطعم شعبي في الرياض").lower()
    assert "Tool" in design_search.recommend("saas analytics dashboard for finance teams")
    assert design_search.search("arabic editorial reading", "fonts", 3)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("selftest OK")
