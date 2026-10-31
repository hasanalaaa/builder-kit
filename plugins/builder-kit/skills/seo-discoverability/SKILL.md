---
name: seo-discoverability
description: Load when building or launching a public site, landing page, blog or store, or when pages don't rank or share badly. Technical SEO, metadata, JSON-LD, Open Graph, hreflang and Arabic SEO, AI search. Triggers: SEO, sitemap, الظهور في جوجل.
---

# SEO and Discoverability

Search engines, social apps and AI assistants all read the same things: server-rendered HTML, a clear title and description, one topic per page, structured data, fast pages, and links that make sense. Most AI-built sites miss them because content is rendered on the client, every page shares one title, and nothing tells crawlers what exists.

| File | Use it for |
|------|-----------|
| `references/seo.md` | Technical SEO, metadata per framework, structured data examples, social cards, multilingual/hreflang and Arabic SEO, local SEO, content and internal linking, AI search, Search Console, launch and migration checklists |
| `scripts/seo_check.py` | Check a built HTML folder or live URL(s): title/description length, canonical, robots noindex, `lang`, viewport, one `h1`, Open Graph/X card, valid JSON-LD, hreflang `x-default`, image alts, duplicate titles; for URLs also `robots.txt` and `sitemap.xml` |

## 1. Rules

1. **Server-render public content** (SSG/ISR/SSR). Content that appears only after client JavaScript is discovered late or not at all, and social/AI crawlers often don't run JS.
2. **Every indexable page has** a unique `<title>` (≤ 60 chars, primary topic first), a meta description (≈ 120–160 chars that earns the click), one `h1`, a self-referencing canonical, `lang`, and Open Graph + X card tags with a 1200×630 image.
3. **One URL per piece of content.** Canonicalize variants (trailing slash, query params, www/non-www, http/https); 301 redirects for moved pages; real 404/410 for gone pages (no "soft 404" 200 pages).
4. **Tell crawlers what exists**: `sitemap.xml` (indexable canonical URLs only, with lastmod), `robots.txt` pointing to it, no accidental `noindex`/`Disallow: /` in production (and do block preview/staging deployments).
5. **Structured data** (JSON-LD) for the entity types you really have; valid and matching visible content.
6. **Multilingual done right**: separate URLs per language, `hreflang` for every alternate + `x-default`, translated titles/descriptions/slugs where useful, Arabic content written for Arabic search intent (not just translated).
7. **Fast and stable**: Core Web Vitals pass (`performance`); mobile-first.
8. **Content answers the searcher's question** better than alternatives: specific, expert, current, with clear headings, internal links to related pages, and descriptive anchor text.
9. **Measure**: Google Search Console and Bing Webmaster Tools verified, sitemap submitted, coverage and query reports reviewed monthly.

## 2. Workflow

1. List page types and their search intent (home, category, product/service, article, location, docs).
2. Implement metadata per page type with the framework's API (`seo.md` §2), structured data per type (§3), OG images (static or generated).
3. Generate sitemap(s) and robots.txt; set canonical rules; redirects map for any changed URLs.
4. i18n: hreflang + localized metadata (`i18n-rtl` §9).
5. Build, then `python3 <skill>/scripts/seo_check.py <build-output-dir>`; after deploy `seo_check.py https://example.com https://example.com/ar`.
6. Verify in Search Console (URL Inspection), Rich Results Test, social debuggers (Facebook Sharing Debugger, LinkedIn Post Inspector).

## 3. Done when

- [ ] `seo_check.py` 0 ERROR on built pages and production URLs.
- [ ] Unique titles/descriptions; one h1; canonicals; OG/X images render in debuggers.
- [ ] sitemap.xml + robots.txt correct in production; previews/staging are noindex.
- [ ] Structured data valid in Rich Results Test.
- [ ] hreflang pairs complete with x-default for multilingual sites.
- [ ] Core Web Vitals good on key templates; Search Console verified with sitemap submitted.
