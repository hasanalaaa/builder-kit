#!/usr/bin/env python3
"""Color contrast checker: WCAG 2.2 ratio + APCA Lc, and OKLCH color math used by palette.py.

Usage:
  contrast.py "#ffffff" "#6b7280"            # one pair (foreground, background)
  contrast.py --tokens src/styles/tokens.css  # every X / X-foreground pair, ring and input, per theme block

Colors: #rgb, #rrggbb, #rrggbbaa, rgb()/rgba(), hsl()/hsla(), bare "H S% L%" (old shadcn), oklch().
Exit code 1 when a required pair fails (text < 4.5:1, ring < 3:1).
"""
import argparse
import math
import re
import sys

# ---------- parsing ----------

def _clamp01(x):
    return min(1.0, max(0.0, x))


def hsl_to_rgb(h, s, l):
    s, l = s / 100, l / 100
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)][int(h % 360 // 60)]
    return tuple(round((v + m) * 255) for v in (r, g, b))


def parse_color(text):
    """Return (r, g, b) 0-255 ints, or None if not a color literal."""
    t = text.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3,8})", t)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        if len(h) in (6, 8):
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        return None
    nums = lambda s: [float(n) for n in re.findall(r"-?\d*\.?\d+", s)]
    if t.startswith("rgb"):
        v = nums(t)
        if "%" in t:
            v = [x * 2.55 for x in v[:3]]
        return tuple(round(x) for x in v[:3]) if len(v) >= 3 else None
    if t.startswith("hsl"):
        v = nums(t)
        return hsl_to_rgb(*v[:3]) if len(v) >= 3 else None
    if t.startswith("oklch"):
        v = nums(t.split("/")[0])
        if len(v) < 3:
            return None
        L = v[0] / 100 if "%" in t.split()[0] else v[0]
        return oklch_to_rgb(L, v[1], v[2])
    m = re.fullmatch(r"(-?\d*\.?\d+)\s+(\d*\.?\d+)%\s+(\d*\.?\d+)%", t)
    if m:
        return hsl_to_rgb(*(float(g) for g in m.groups()))
    return None


def rgb_to_hex(rgb):
    return "#" + "".join(f"{int(round(c)):02x}" for c in rgb)

# ---------- WCAG ----------

def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def wcag_ratio(fg, bg):
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)

# ---------- APCA (0.0.98G-4g constants) ----------

def apca(fg, bg):
    """Lc value: positive = dark text on light bg, negative = light text on dark bg."""
    def y(rgb):
        v = 0.2126729 * (rgb[0] / 255) ** 2.4 + 0.7151522 * (rgb[1] / 255) ** 2.4 + 0.0721750 * (rgb[2] / 255) ** 2.4
        return v if v > 0.022 else v + (0.022 - v) ** 1.414
    yt, yb = y(fg), y(bg)
    if abs(yb - yt) < 0.0005:
        return 0.0
    if yb > yt:
        s = (yb ** 0.56 - yt ** 0.57) * 1.14
        return 0.0 if s < 0.1 else (s - 0.027) * 100
    s = (yb ** 0.65 - yt ** 0.62) * 1.14
    return 0.0 if s > -0.1 else (s + 0.027) * 100

# ---------- OKLCH ----------

def oklch_to_linear(L, C, H):
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
            -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
            -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)


def in_gamut(L, C, H, eps=1e-4):
    return all(-eps <= v <= 1 + eps for v in oklch_to_linear(L, C, H))


def _gamma(v):
    v = _clamp01(v)
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def oklch_to_rgb(L, C, H):
    return tuple(round(_gamma(v) * 255) for v in oklch_to_linear(L, C, H))


def rgb_to_oklch(rgb):
    r, g, b = (_lin(c) for c in rgb)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def fit_gamut(L, C, H):
    """Largest chroma <= C that stays inside sRGB at this L and H."""
    if in_gamut(L, C, H):
        return L, C, H
    lo, hi = 0.0, C
    for _ in range(24):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if in_gamut(L, mid, H) else (lo, mid)
    return L, lo, H

# ---------- token files ----------

BLOCK = re.compile(r"([^{};]+)\{([^{}]*)\}")
DECL = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
FG_SUFFIXES = ("-foreground", "-fg")


def parse_blocks(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return [(sel.strip().split("\n")[-1].strip(), dict(DECL.findall(body))) for sel, body in BLOCK.findall(css)]


def resolve(name, scope, depth=0):
    val = scope.get(name)
    if val is None or depth > 8:
        return None
    m = re.fullmatch(r"\s*var\((--[\w-]+)(?:,[^)]*)?\)\s*", val)
    return resolve(m.group(1), scope, depth + 1) if m else parse_color(val)


def token_pairs(scope):
    """Yield (label, fg_name, bg_name, minimum, required)."""
    names = set(scope)
    for prefix in ("--color-", "--"):
        if prefix + "foreground" in names and prefix + "background" in names:
            yield "foreground/background", prefix + "foreground", prefix + "background", 4.5, True
    for n in sorted(names):
        for suf in FG_SUFFIXES:
            base = n[: -len(suf)]
            if n.endswith(suf) and base in names and not base.endswith("-"):
                yield f"{n[2:]}/{base[2:]}", n, base, 4.5, True
        if n.endswith("muted-foreground"):
            for bg in ("--color-background", "--background"):
                if bg in names:
                    yield f"{n[2:]}/{bg[2:]}", n, bg, 4.5, True
    for prefix in ("--color-", "--"):
        bg = prefix + "background"
        if prefix + "ring" in names and bg in names:
            yield "ring/background", prefix + "ring", bg, 3.0, True
        if prefix + "input" in names and bg in names:
            yield "input/background (field boundary)", prefix + "input", bg, 3.0, False


def check_tokens(css):
    """Return list of (block, label, ratio, minimum, required, ok)."""
    blocks = parse_blocks(css)
    root = {}
    for sel, decls in blocks:
        s = sel.replace(" ", "")
        if s in (":root", "html", ":host", ":root,:host") or s.startswith("@theme"):
            root.update(decls)
    results, seen = [], set()
    for sel, decls in blocks:
        scope = {**root, **decls}
        for label, fg, bg, minimum, required in token_pairs(scope):
            if fg not in decls and bg not in decls:
                continue
            key = (sel, label)
            c1, c2 = resolve(fg, scope), resolve(bg, scope)
            if not c1 or not c2 or key in seen:
                continue
            seen.add(key)
            r = wcag_ratio(c1, c2)
            results.append((sel, label, r, minimum, required, r >= minimum))
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("colors", nargs="*", help="foreground background")
    p.add_argument("--tokens", help="CSS file with custom properties")
    a = p.parse_args()
    if a.tokens:
        with open(a.tokens, encoding="utf-8") as f:
            results = check_tokens(f.read())
        if not results:
            print("No color token pairs found (expected X / X-foreground custom properties).")
            return 0
        fails = 0
        for sel, label, r, minimum, required, ok in results:
            tag = "PASS" if ok else ("FAIL" if required else "WARN")
            fails += tag == "FAIL"
            print(f"{tag:4} {r:5.2f}:1 (min {minimum}) {sel} · {label}")
        print(f"\n{len(results)} pairs · {fails} failing")
        return 1 if fails else 0
    if len(a.colors) != 2:
        p.error("give two colors or --tokens FILE")
    fg, bg = (parse_color(c) for c in a.colors)
    if not fg or not bg:
        p.error("could not parse a color")
    r, lc = wcag_ratio(fg, bg), apca(fg, bg)
    verdict = "AA body" if r >= 4.5 else "AA large/UI only" if r >= 3 else "FAIL"
    print(f"WCAG {r:.2f}:1 ({verdict}) · APCA Lc {lc:.1f} · {rgb_to_hex(fg)} on {rgb_to_hex(bg)}")
    return 0 if r >= 4.5 else 1


if __name__ == "__main__":
    sys.exit(main())
