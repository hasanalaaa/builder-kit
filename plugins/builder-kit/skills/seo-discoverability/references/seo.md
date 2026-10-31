# SEO reference

## 1. Technical foundations

- **Rendering**: public pages SSG/ISR/SSR; check "View Source" contains the content, not an empty root div.
- **Status codes**: 200 for real pages, 301 for permanent moves, 404/410 for missing, 5xx only on real errors; no redirect chains (> 1 hop).
- **HTTPS everywhere**, one host (redirect www ↔ apex), HSTS.
- **Canonical**: absolute URL, self-referencing on canonical pages; filters/sort/pagination params canonicalize to the clean URL unless the variant deserves indexing.
- **Pagination**: crawlable links (`<a href="?page=2">`), each page self-canonical.
- **robots.txt**: allow assets (CSS/JS); disallow only private paths (`/api/`, `/admin/`, `/account/`); `Sitemap: https://…/sitemap.xml`.
- **Meta robots / X-Robots-Tag**: `noindex` on thin/private/duplicate pages (search results, cart, account), on preview deployments (Vercel adds it for preview URLs; verify) and on staging.
- **Sitemaps**: only canonical, indexable, 200 URLs; split > 50k URLs; `lastmod` accurate; per-locale entries with alternates.
- **Internal links**: real `<a href>` elements (not JS click handlers), descriptive anchors, breadcrumbs, related content, no orphan pages.
- **JavaScript**: don't depend on client-only routing for discoverability; links must work without JS; lazy-loaded content must exist in the DOM or SSR.
- **Images**: descriptive file names, `alt`, modern formats, `width/height`; image sitemaps for image-heavy sites.
- **Video**: `VideoObject` schema, thumbnails, transcripts.

## 2. Metadata by framework

**Next.js App Router**
```ts
export const metadata: Metadata = {
  metadataBase: new URL("https://example.com"),
  title: { default: "Rawdah", template: "%s · Rawdah" },
  description: "Daily updates from your child's nursery, in Arabic and English.",
  alternates: { canonical: "/", languages: { ar: "/ar", en: "/en", "x-default": "/" } },
  openGraph: { type: "website", siteName: "Rawdah", images: ["/og.png"] },
  twitter: { card: "summary_large_image" },
};
export async function generateMetadata({ params }) { /* per page: title, description, canonical, OG */ }
```
- `app/sitemap.ts`, `app/robots.ts`, `app/opengraph-image.tsx` (generated OG images with `ImageResponse`), `app/manifest.ts`.

**Astro**: `<head>` in layout with props; `@astrojs/sitemap`; `astro-seo` helper.
**Nuxt**: `useSeoMeta`, `@nuxtjs/sitemap`, `@nuxtjs/robots`, Nuxt SEO module.
**SvelteKit**: `<svelte:head>` per page; prerender public routes.
**SPA (Vite)**: pre-render marketing routes (vite-plugin-ssg, react-snap) or move marketing to Astro/Next; at minimum per-route `document.title` + meta via react-helmet-async (weaker).

## 3. Structured data (JSON-LD)

Use types that match real content; validate with Rich Results Test and Schema.org validator.
```html
<script type="application/ld+json">
{ "@context": "https://schema.org", "@type": "Organization", "name": "Rawdah", "url": "https://example.com",
  "logo": "https://example.com/logo.png", "sameAs": ["https://x.com/rawdah", "https://www.linkedin.com/company/rawdah"] }
</script>
```
| Page | Types |
|------|-------|
| Home | Organization (+ WebSite with SearchAction if you have site search) |
| Product | Product with Offer (price, currency, availability), AggregateRating (only real reviews) |
| Article/blog | Article / BlogPosting (headline, author Person, datePublished, dateModified, image) |
| Local business | LocalBusiness subtype (Restaurant, Dentist…) with address, geo, openingHours, telephone |
| FAQ section | FAQPage (rich results now limited to authoritative sites, still useful for clarity) |
| Breadcrumbs | BreadcrumbList |
| Software/app | SoftwareApplication / MobileApplication (rating, price, OS) |
| Events | Event (startDate, location, offers) |
| Courses | Course |
| Video | VideoObject |

## 4. Social previews

- `og:title`, `og:description`, `og:image` (1200×630, < 5 MB, absolute URL), `og:url`, `og:type`, `og:locale` (`ar_SA`, `en_US`) + `og:locale:alternate`; `twitter:card=summary_large_image`.
- Arabic OG images: render Arabic text with a proper Arabic font in the image generator (shaping/RTL), test in WhatsApp, X, LinkedIn, Slack, iMessage previews.
- Debug: Facebook Sharing Debugger, LinkedIn Post Inspector; caches need re-scraping after changes.

## 5. Multilingual and Arabic SEO

- URL per language (`/ar/…`, `/en/…`); never switch language only by cookie/JS on the same URL for public content.
- `hreflang` on every page for every alternate, reciprocal, plus `x-default`; region variants when content differs (`ar-SA`, `ar-AE`).
- Translate title, description, headings, alt text, slugs (Arabic slugs are fine, percent-encoded in URLs; or transliterated) and structured data.
- Arabic keyword research: users search in Arabic script, dialect words, and Arabizi/English mixes; check search terms in Search Console and keyword tools for the target country; cover spelling variants (ة/ه, ى/ي, أ/ا) naturally in content.
- Dates/numbers in the locale's format; `dir="rtl"` and `lang="ar"` on Arabic pages.
- Separate Search Console properties or filters per country/language to measure.

## 6. Local SEO

- Google Business Profile complete (category, hours, photos, services, posts, Q&A), consistent NAP (name, address, phone) across site and directories, LocalBusiness schema, location pages for multi-location businesses, reviews responded to, embedded map with facade.
- Apple Business Connect, Bing Places; regional directories relevant to the market.

## 7. Content and on-page

- One primary topic/intent per page; title and h1 aligned but not identical necessarily.
- Answer the question early (summary first), then depth: headings that mirror sub-questions, tables, steps, examples, original data/images.
- E-E-A-T signals: real authors with bios, dates updated, sources cited, about/contact pages, policies.
- Avoid thin/duplicate pages (tag pages with one post, location pages with swapped city names only).
- Internal links from strong pages to important pages; update old posts to link to new ones.
- AI-generated content: allowed when helpful and reviewed; mass-produced low-value pages are spam.

## 8. AI search (answer engines)

- Same foundations: crawlable server-rendered content, clear structure, factual specifics, citations, up-to-date dates, structured data.
- Allow or block AI crawlers deliberately in robots.txt (e.g. `GPTBot`, `ClaudeBot`, `Google-Extended`, `PerplexityBot`, `CCBot`) per business decision.
- Clear "about" facts (who, what, where, pricing) in plain text that can be quoted.
- `llms.txt` (a community proposal for an LLM-friendly site summary) is optional and low-cost; don't rely on it.
- Track referrals from AI assistants in analytics.

## 9. Measurement

- Google Search Console: verify domain property (DNS), submit sitemap, watch Pages (indexing) report, Core Web Vitals, Enhancements (structured data), Performance queries/CTR.
- Bing Webmaster Tools (also feeds some AI products), Yandex if relevant.
- Analytics: organic landing pages, conversions from organic.
- Monthly: fix coverage errors, improve titles/descriptions for high-impression low-CTR queries, refresh decaying content.

## 10. Launch checklist

- [ ] Production not blocked (robots.txt, meta robots, `X-Robots-Tag`); staging/previews blocked.
- [ ] Titles/descriptions unique; canonicals; hreflang; OG images.
- [ ] sitemap.xml live and submitted; robots.txt references it.
- [ ] 404 page returns 404; redirects from old URLs (if any) are 301 and single-hop.
- [ ] Structured data valid; favicon, apple-touch-icon, web manifest.
- [ ] Core Web Vitals good on templates; mobile-friendly.
- [ ] Analytics + Search Console + Bing verified.

## 11. Site migration (domain/URL changes)

Map every old URL → new URL; 301 one hop; update internal links, canonicals, sitemaps, hreflang; keep old domain redirecting for at least a year; Search Console Change of Address for domain moves; monitor indexing and traffic daily for weeks.
