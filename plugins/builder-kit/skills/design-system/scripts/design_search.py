#!/usr/bin/env python3
"""Search the design database, or get a starting design brief for a product.

Usage:
  design_search.py --recommend "Arabic food delivery app for families in Riyadh"
  design_search.py "calm health" --domain palettes
  design_search.py "arabic editorial" --domain fonts -n 5
Domains: products, styles, palettes, fonts, ux-rules, landing, charts (default: all).
Arabic keywords are understood for common product types.
"""
import argparse
import csv
import math
import os
import re
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DOMAINS = ["products", "styles", "palettes", "fonts", "ux-rules", "landing", "charts"]
WEIGHTS = {"keywords": 3.0, "product": 2.0, "style": 2.0, "name": 2.0, "pattern": 2.0, "question": 2.0, "category": 1.5, "rule": 1.5, "mood": 1.5}
AR = {
    "مطعم": "restaurant food", "مطاعم": "restaurant food", "كافيه": "cafe coffee", "قهوة": "coffee", "متجر": "store ecommerce shop",
    "تسوق": "shopping ecommerce", "تطبيق": "app mobile", "موقع": "website landing", "عيادة": "clinic health", "طبي": "medical health",
    "صحة": "health", "مستشفى": "hospital health", "بنك": "bank finance", "مالي": "finance fintech", "محفظة": "wallet fintech",
    "دفع": "payments fintech", "حكومي": "government", "حكومة": "government", "وزارة": "government ministry", "تعليم": "education learning",
    "تعليمي": "education", "دورة": "course education", "أطفال": "kids children", "اطفال": "kids children", "عقار": "real estate property",
    "عقارات": "real estate property", "فندق": "hotel hospitality", "سفر": "travel", "سياحة": "travel tourism", "رياضة": "fitness sports",
    "لياقة": "fitness", "أخبار": "news media", "اخبار": "news media", "مجلة": "magazine editorial", "مدونة": "blog editorial",
    "شركة": "corporate company", "ناشئة": "startup saas", "لوحة": "dashboard", "تحكم": "dashboard admin", "إدارة": "admin management",
    "ذكاء": "ai", "اصطناعي": "ai", "توصيل": "delivery", "قرآن": "quran islamic", "صلاة": "prayer islamic", "فعالية": "event",
    "مؤتمر": "conference event", "موضة": "fashion", "تجميل": "beauty", "عطور": "perfume luxury", "فاخر": "luxury premium",
    "ألعاب": "gaming game", "العاب": "gaming game", "خيري": "charity nonprofit", "تبرع": "donation nonprofit", "شحن": "logistics shipping",
    "سيارات": "automotive car", "وظائف": "jobs hr recruiting", "محاماة": "law legal", "استشارات": "consulting", "مطور": "developer",
    "مطورين": "developer api", "بيانات": "data analytics", "تحليلات": "analytics dashboard", "هادئ": "calm", "فخم": "luxury premium",
    "عصري": "modern", "بسيط": "minimal clean", "مرح": "playful fun", "داكن": "dark", "تراث": "heritage arabic", "عربي": "arabic",
    "طعام": "food", "أكل": "food", "اكل": "food", "عائلات": "family", "عائلة": "family", "عائلي": "family", "مدرسة": "school education",
    "طلاب": "students education", "حجز": "booking", "حجوزات": "booking", "متاجر": "store ecommerce", "منصة": "platform", "مجتمع": "community social",
    "تواصل": "social", "موسيقى": "music", "بودكاست": "podcast", "فيديو": "video media", "مقهى": "cafe coffee", "مخبز": "bakery",
}


def load(domain):
    with open(os.path.join(DATA, f"{domain}.csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


AR_PREFIXES = ("وال", "بال", "لل", "ال", "و", "ب", "ل")


def ar_lookup(word):
    for cand in [word] + [word[len(p):] for p in AR_PREFIXES if word.startswith(p) and len(word) - len(p) > 2]:
        if cand in AR:
            return AR[cand]
    return ""


def tokens(text):
    words = [t for t in re.split(r"[^a-z0-9؀-ۿ]+", text.lower()) if len(t) > 1]
    extra = " ".join(ar_lookup(w) for w in words if re.match(r"[؀-ۿ]", w))
    return words + extra.split()


def search(query, domain, n=5):
    rows = load(domain)
    q = tokens(query)
    docs = [{k: tokens(v or "") for k, v in r.items()} for r in rows]
    df = {t: sum(any(t in field for field in d.values()) for d in docs) for t in set(q)}
    scored = []
    for row, d in zip(rows, docs):
        score = 0.0
        for t in q:
            if not df[t]:
                continue
            idf = math.log(1 + len(rows) / df[t])
            score += sum(WEIGHTS.get(k, 1.0) * idf for k, field in d.items() if t in field)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:n]]


def by_id(domain, ids):
    rows = {r["id"]: r for r in load(domain)}
    return [rows[i] for i in ids if i in rows]


def show(row, keys=None):
    keys = keys or [k for k in row if k != "id"]
    return "; ".join(f"{k}: {row[k]}" for k in keys if row.get(k))


def recommend(brief):
    products = search(brief, "products", 3)
    p = products[0] if products else by_id("products", ["saas-b2b"])[0]
    out = [f"# Design starting point for: {brief}", "",
           f"**Archetype:** {p['product']} (`{p['id']}`) · **Surface mode:** {p['surface_mode']}"]
    if len(products) > 1:
        out.append("Other close matches: " + ", ".join(f"{r['product']} (`{r['id']}`)" for r in products[1:]))
    out += [f"**Key points:** {p['key_points']}", f"**Avoid:** {p['avoid']}", "", "## Visual worlds (pick one, see direction.md §2)"]
    for s in by_id("styles", p["styles"].split(";")):
        out.append(f"- **{s['style']}** — {s['look']} · radius {s['radius']} · motion {s['motion']} · a11y risk {s['a11y_risk']}")
    out.append("\n## Palette seeds (generate tokens with palette.py)")
    pals = by_id("palettes", p["palettes"].split(";"))
    extra = [r for r in search(brief, "palettes", 3) if r not in pals]
    for r in pals + extra[:1]:
        out.append(f"- **{r['name']}** ({r['mood']}) brand {r['brand_hex']} accent {r['accent_hex']}"
                   f"{' · dark-first' if r['dark_first'] == 'yes' else ''} → `palette.py --brand \"{r['brand_hex']}\" --name {r['id']}`")
    out.append("\n## Type (Latin + Arabic)")
    for f in by_id("fonts", p["fonts"].split(";")):
        out.append(f"- **{f['name']}**: display {f['latin_display']} / {f['arabic_display']} · body {f['latin_body']} / {f['arabic_body']} · mono {f['mono']} — {f['notes']}")
    if p["landing"]:
        for l in by_id("landing", [p["landing"]]):
            out += ["\n## Landing structure", f"**{l['pattern']}**: {l['sections']}", f"CTA: {l['cta']} · {l['notes']}"]
    out.append("\n## UX rules that matter most here")
    rules = search(brief + " " + p["keywords"], "ux-rules", 8)
    must = by_id("ux-rules", ["A01", "A02", "A03", "R01", "L01"])
    for r in rules + [m for m in must if m not in rules]:
        out.append(f"- [{r['id']} {r['severity']}] {r['rule']}: {r['do']} (not: {r['dont']})")
    out += ["\n## Next", "1. Propose 2–3 directions (direction.md §3) using the worlds above.",
            "2. Generate tokens with palette.py; set type scale (typography.md).", "3. Write DESIGN.md; read craft-floor.md before building."]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?")
    ap.add_argument("--recommend", metavar="BRIEF")
    ap.add_argument("--domain", choices=DOMAINS)
    ap.add_argument("-n", type=int, default=5)
    a = ap.parse_args()
    if a.recommend:
        print(recommend(a.recommend))
        return 0
    if not a.query:
        ap.error("give a query or --recommend BRIEF")
    for d in [a.domain] if a.domain else DOMAINS:
        hits = search(a.query, d, a.n)
        if hits:
            print(f"\n## {d}")
            for r in hits:
                print(f"- `{r['id']}` {show(r)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
