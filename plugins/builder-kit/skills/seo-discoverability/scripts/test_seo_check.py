#!/usr/bin/env python3
"""Self-test for seo_check (offline). Run: python3 test_seo_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_check  # noqa: E402

BAD = """<html><head><title>Hi</title><meta name="robots" content="noindex">
<link rel="alternate" hreflang="ar" href="/ar"><script type="application/ld+json">{ "@type": "Organization", }</script>
</head><body><h1>A</h1><h1>B</h1><img src="a.png"></body></html>"""
GOOD = """<html lang="ar" dir="rtl"><head><title>روضة · تحديثات يومية من الحضانة</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="تابع وجبات طفلك ونومه وصوره يوميًا من الحضانة، بالعربية والإنجليزية، بأمان وخصوصية كاملة لكل عائلة.">
<link rel="canonical" href="https://example.com/ar"><link rel="alternate" hreflang="ar" href="https://example.com/ar">
<link rel="alternate" hreflang="en" href="https://example.com/en"><link rel="alternate" hreflang="x-default" href="https://example.com/">
<meta property="og:title" content="روضة"><meta property="og:description" content="تحديثات يومية"><meta property="og:image" content="https://example.com/og.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Rawdah"}</script>
</head><body><h1>روضة</h1><img src="a.png" alt="طفل يلعب"></body></html>"""


def rules(pages):
    with tempfile.TemporaryDirectory() as d:
        for name, html in pages.items():
            with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                f.write(html)
        return {f[1] for f in seo_check.run([d])}


if __name__ == "__main__":
    got = rules({"index.html": BAD, "about.html": BAD})
    want = {"title-length", "no-description", "no-lang", "no-viewport", "noindex", "no-canonical", "hreflang-no-default",
            "no-open-graph", "no-twitter-card", "h1-count", "img-alt", "jsonld-invalid", "duplicate-title"}
    assert want <= got, sorted(want - got)
    got = rules({"index.html": GOOD})
    assert not got, sorted(got)
    print("selftest OK")
