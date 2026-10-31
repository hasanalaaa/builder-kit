#!/usr/bin/env python3
"""seo_check: check SEO and social-preview basics in built HTML or live URLs.

Usage:
  seo_check.py out/                       # every *.html under a build output folder
  seo_check.py https://example.com https://example.com/ar   # live pages (+ robots.txt and sitemap.xml)
Exit 1 on any ERROR.
"""
import argparse
import collections
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; builder-kit-seo-check/1.0)"


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.in_title, self.in_ld = "", False, False
        self.meta, self.links, self.ld, self.h1, self.imgs_no_alt, self.html_attrs = {}, [], [], 0, 0, {}
        self._ld_buf = ""

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.html_attrs = a
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and "alt" not in a:
            self.imgs_no_alt += 1
        elif tag == "script" and a.get("type") == "application/ld+json":
            self.in_ld, self._ld_buf = True, ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "script" and self.in_ld:
            self.ld.append(self._ld_buf)
            self.in_ld = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_ld:
            self._ld_buf += data


def check_page(where, html, findings):
    p = Page()
    p.feed(html)
    add = lambda level, rule, msg: findings.append((level, rule, where, msg))
    title = p.title.strip()
    if not title:
        add("ERROR", "no-title", "Missing <title>")
    elif not 15 <= len(title) <= 60:
        add("WARN", "title-length", f"Title is {len(title)} chars (aim 15–60): {title[:70]}")
    desc = p.meta.get("description", "").strip()
    if not desc:
        add("WARN", "no-description", "Missing meta description")
    elif not 50 <= len(desc) <= 165:
        add("WARN", "description-length", f"Description is {len(desc)} chars (aim ~120–160)")
    if not p.html_attrs.get("lang"):
        add("ERROR", "no-lang", "<html> has no lang")
    if "viewport" not in p.meta:
        add("ERROR", "no-viewport", "Missing meta viewport (mobile-first indexing)")
    robots = p.meta.get("robots", "") + " " + p.meta.get("googlebot", "")
    if "noindex" in robots.lower():
        add("WARN", "noindex", "Page is noindex: intended? (fine for private/preview pages only)")
    rels = collections.defaultdict(list)
    for link in p.links:
        for r in link.get("rel", "").lower().split():
            rels[r].append(link)
    if not rels.get("canonical"):
        add("WARN", "no-canonical", "No rel=canonical")
    hreflangs = [l.get("hreflang", "").lower() for l in rels.get("alternate", []) if l.get("hreflang")]
    if hreflangs and "x-default" not in hreflangs:
        add("WARN", "hreflang-no-default", f"hreflang set ({', '.join(hreflangs)}) without x-default")
    for key in ("og:title", "og:description", "og:image"):
        if key not in p.meta:
            add("WARN", "no-open-graph", f"Missing {key}")
    if "twitter:card" not in p.meta:
        add("WARN", "no-twitter-card", "Missing twitter:card")
    if p.h1 != 1:
        add("WARN", "h1-count", f"{p.h1} <h1> elements (want exactly 1)")
    if p.imgs_no_alt:
        add("WARN", "img-alt", f"{p.imgs_no_alt} <img> without alt")
    for block in p.ld:
        try:
            data = json.loads(block)
            items = data if isinstance(data, list) else [data]
            if not all(isinstance(i, dict) and ("@type" in i or "@graph" in i) for i in items):
                add("WARN", "jsonld-type", "JSON-LD without @type")
        except json.JSONDecodeError as e:
            add("ERROR", "jsonld-invalid", f"Invalid JSON-LD: {e.msg} at line {e.lineno}")
    return title


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # security-scan: ignore (user-given URL, read-only check)
        return r.status, r.read().decode("utf-8", "ignore"), dict(r.headers)


def check_site(url, findings):
    base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(url))
    sitemap = base + "/sitemap.xml"
    try:
        status, body, _ = fetch(base + "/robots.txt")
        lines = [l.strip().lower() for l in body.splitlines()]
        declared = [l.split(":", 1)[1].strip() for l in body.splitlines() if l.strip().lower().startswith("sitemap:")]
        sitemap = declared[0] if declared else sitemap
        if status != 200:
            findings.append(("WARN", "no-robots", base, "robots.txt not found"))
        else:
            if "disallow: /" in lines and "user-agent: *" in lines:
                findings.append(("ERROR", "robots-blocks-all", base, "robots.txt blocks everything (Disallow: /)"))
            if not any(l.startswith("sitemap:") for l in lines):
                findings.append(("WARN", "robots-no-sitemap", base, "robots.txt has no Sitemap: line"))
    except (urllib.error.URLError, OSError) as e:
        findings.append(("WARN", "no-robots", base, f"robots.txt not reachable ({e})"))
    try:
        status, body, _ = fetch(sitemap)
        if status != 200 or "<urlset" not in body and "<sitemapindex" not in body:
            findings.append(("WARN", "no-sitemap", sitemap, "sitemap missing or not a sitemap"))
    except (urllib.error.URLError, OSError):
        findings.append(("WARN", "no-sitemap", sitemap, "sitemap not reachable"))


def run(targets):
    findings, titles, sites = [], collections.defaultdict(list), set()
    for t in targets:
        if t.startswith(("http://", "https://")):
            try:
                status, html, headers = fetch(t)
            except (urllib.error.URLError, OSError) as e:
                findings.append(("ERROR", "fetch-failed", t, str(e)))
                continue
            if "noindex" in headers.get("X-Robots-Tag", "").lower():
                findings.append(("WARN", "noindex", t, "X-Robots-Tag noindex header"))
            titles[check_page(t, html, findings)].append(t)
            sites.add(urllib.parse.urlparse(t).netloc)
            if len(sites) == 1 and t == targets[0]:
                check_site(t, findings)
        else:
            for d, _, files in os.walk(t):
                for f in files:
                    if f.endswith(".html") and not f.startswith(("404", "500", "_")):
                        path = os.path.join(d, f)
                        with open(path, encoding="utf-8", errors="ignore") as fh:
                            rel = os.path.relpath(path, t)
                            titles[check_page(rel, fh.read(), findings)].append(rel)
    for title, pages in titles.items():
        if title and len(pages) > 1:
            findings.append(("WARN", "duplicate-title", ", ".join(pages[:4]), f"{len(pages)} pages share the title '{title[:50]}'"))
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("targets", nargs="+", help="build folder(s) or URL(s)")
    a = p.parse_args()
    findings = run(a.targets)
    counts = collections.Counter()
    for level, rule, where, msg in sorted(findings, key=lambda f: (f[0] != "ERROR", f[1], f[2])):
        counts[rule] += 1
        if counts[rule] <= 30:
            print(f"{level:5} {rule:20} {where}  {msg}")
    errors = sum(f[0] == "ERROR" for f in findings)
    print(f"\nseo_check: {errors} ERROR, {len(findings) - errors} WARN")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
