#!/usr/bin/env python3
"""Generate a contrast-checked OKLCH palette and semantic light/dark tokens from one brand color.

Usage:
  palette.py --brand "#2563EB"                       # CSS custom properties (--color-*)
  palette.py --brand "#2563EB" --format tailwind     # Tailwind v4 @theme block + .dark overrides
  palette.py --hue 160 --chroma 0.12 --format shadcn # shadcn/ui variable names
  palette.py --brand "#0F766E" --format json         # for React Native / Swift / Compose

Every foreground/background pair is pushed until it reaches WCAG AA (text 4.5:1, ring 3:1).
The exact brand color is kept as --color-brand; --color-primary is the brand or the nearest step that passes.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contrast import fit_gamut, oklch_to_rgb, parse_color, rgb_to_hex, rgb_to_oklch, wcag_ratio  # noqa: E402

STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
L_COLOR = [0.975, 0.945, 0.895, 0.825, 0.735, 0.645, 0.555, 0.475, 0.395, 0.315, 0.245]
C_CURVE = [0.10, 0.20, 0.40, 0.65, 0.85, 1.00, 1.00, 0.92, 0.80, 0.65, 0.50]
L_NEUTRAL = [0.985, 0.965, 0.92, 0.87, 0.71, 0.555, 0.445, 0.37, 0.27, 0.21, 0.155]
SEMANTIC = {"success": (150, 0.15), "warning": (75, 0.16), "danger": (27, 0.19), "info": (245, 0.14)}
WHITE = (1.0, 0.0, 0.0)


def scale(hue, chroma, lightness=L_COLOR, curve=C_CURVE):
    return {s: fit_gamut(l, chroma * c, hue) for s, l, c in zip(STEPS, lightness, curve)}


def neutral(hue, chroma):
    return {s: fit_gamut(l, chroma, hue) for s, l in zip(STEPS, L_NEUTRAL)}


def rgb(c):
    return oklch_to_rgb(*c)


def ratio(a, b):
    return wcag_ratio(rgb(a), rgb(b))


def push(fg, bg, minimum):
    """Move fg lightness away from bg until the pair passes."""
    L, C, H = fg
    direction = 1 if rgb_to_oklch(rgb(bg))[0] < 0.6 else -1
    while ratio((L, C, H), bg) < minimum and 0.0 < L < 1.0:
        L = min(1.0, max(0.0, L + 0.01 * direction))
        L, C, H = fit_gamut(L, C, H)
    return (L, C, H)


def best_on(bg, light_fg, dark_fg):
    return light_fg if ratio(light_fg, bg) >= ratio(dark_fg, bg) else dark_fg


def solid_pair(bg, light_fg, dark_fg, minimum=4.5):
    """Pick the better foreground for a filled surface; darken/lighten the surface if neither passes."""
    fg = best_on(bg, light_fg, dark_fg)
    L, C, H = bg
    step = -0.01 if fg is light_fg else 0.01
    while ratio(fg, (L, C, H)) < minimum and 0.0 < L < 1.0:
        L, C, H = fit_gamut(L + step, C, H)
    return (L, C, H), fg


def build(hue, chroma, brand=None, neutral_chroma=0.012):
    brand_scale = scale(hue, chroma)
    gray = neutral(hue, neutral_chroma)
    sem = {k: scale(h, c) for k, (h, c) in SEMANTIC.items()}
    chart_hues = [hue, (hue + 150) % 360, (hue + 75) % 360, (hue + 220) % 360, (hue + 300) % 360]

    def theme(dark):
        g = gray
        bg, fg = (g[950], g[50]) if dark else (g[50], g[950])
        card = g[900] if dark else WHITE
        t = {"background": bg, "foreground": fg, "card": card, "card-foreground": fg,
             "popover": card, "popover-foreground": fg}
        start = brand if (brand and not dark) else brand_scale[400 if dark else 600]
        t["primary"], t["primary-foreground"] = solid_pair(start, g[50], g[950])
        t["secondary"] = g[800] if dark else g[100]
        t["secondary-foreground"] = push(g[50] if dark else g[900], t["secondary"], 4.5)
        t["muted"] = g[800] if dark else g[100]
        t["muted-foreground"] = push(g[400] if dark else g[600], t["muted"], 4.5)
        t["muted-foreground"] = push(t["muted-foreground"], bg, 4.5)
        t["accent"] = brand_scale[900] if dark else brand_scale[100]
        t["accent-foreground"] = push(brand_scale[100] if dark else brand_scale[900], t["accent"], 4.5)
        for name, key in (("destructive", "danger"), ("success", "success"), ("warning", "warning"), ("info", "info")):
            t[name], t[name + "-foreground"] = solid_pair(sem[key][500 if dark else 600], g[50], g[950])
        t["border"] = g[800] if dark else g[200]
        t["input"] = push(g[700] if dark else g[400], bg, 3.0)
        t["ring"] = push(brand_scale[400 if dark else 500], bg, 3.0)
        for i, h in enumerate(chart_hues, 1):
            t[f"chart-{i}"] = push(fit_gamut(0.72 if dark else 0.62, 0.15, h), bg, 3.0)
        return t

    return {"brand": brand or brand_scale[600], "scales": {"brand": brand_scale, "neutral": gray, **sem},
            "light": theme(False), "dark": theme(True)}


def fmt(c):
    return f"oklch({c[0]:.3f} {c[1]:.3f} {c[2]:.1f})"


def report(t):
    lines = []
    for k, v in t.items():
        if k.endswith("-foreground"):
            lines.append(f"{k[:-11]} {ratio(v, t[k[:-11]]):.2f}")
    lines.append(f"muted-fg/bg {ratio(t['muted-foreground'], t['background']):.2f}")
    lines.append(f"ring/bg {ratio(t['ring'], t['background']):.2f}")
    return "contrast: " + " · ".join(lines)


def render(p, style, name):
    if style == "json":
        out = {"name": name, "brand": rgb_to_hex(rgb(p["brand"]))}
        out["scales"] = {k: {s: rgb_to_hex(rgb(c)) for s, c in v.items()} for k, v in p["scales"].items()}
        for mode in ("light", "dark"):
            out[mode] = {k: rgb_to_hex(rgb(c)) for k, c in p[mode].items()}
        return json.dumps(out, indent=2)
    pre = "--" if style == "shadcn" else "--color-"
    root = [f"  {pre}brand: {fmt(p['brand'])};"]
    for sname, sc in p["scales"].items():
        root += [f"  {pre}{sname}-{s}: {fmt(c)};" for s, c in sc.items()]
    light = [f"  {pre}{k}: {fmt(c)};" for k, c in p["light"].items()]
    dark = [f"  {pre}{k}: {fmt(c)};" for k, c in p["dark"].items()]
    head = f"/* {name}: generated by palette.py · {report(p['light'])} */\n/* dark {report(p['dark'])} */\n"
    if style == "tailwind":
        return (head + "@theme {\n" + "\n".join(root + light) + "\n}\n\n.dark {\n" + "\n".join(dark) + "\n}\n"
                "@custom-variant dark (&:where(.dark, .dark *));\n")
    return (head + ":root {\n  color-scheme: light dark;\n" + "\n".join(root + light) + "\n}\n\n.dark {\n"
            + "\n".join(dark) + "\n}\n\n@media (prefers-color-scheme: dark) {\n  :root:not(.light) {\n"
            + "\n".join("  " + d for d in dark) + "\n  }\n}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brand", help="brand color (hex, rgb(), oklch())")
    ap.add_argument("--hue", type=float, help="OKLCH hue 0-360 when no brand color")
    ap.add_argument("--chroma", type=float, default=0.16, help="peak chroma for --hue (default 0.16)")
    ap.add_argument("--neutral-chroma", type=float, default=0.012, help="tint of the gray scale (0 = pure gray)")
    ap.add_argument("--name", default="palette")
    ap.add_argument("--format", choices=["css", "tailwind", "shadcn", "json"], default="css")
    a = ap.parse_args()
    if a.brand:
        rgbv = parse_color(a.brand)
        if not rgbv:
            ap.error(f"cannot parse --brand {a.brand}")
        L, C, H = rgb_to_oklch(rgbv)
        p = build(H, max(C, 0.04), brand=(L, C, H), neutral_chroma=a.neutral_chroma)
    elif a.hue is not None:
        p = build(a.hue % 360, a.chroma, neutral_chroma=a.neutral_chroma)
    else:
        ap.error("give --brand or --hue")
    print(render(p, a.format, a.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
