# Performance playbook

## 1. Measuring

- **Field (real users)**: PageSpeed Insights (CrUX data for popular URLs), Search Console Core Web Vitals report, `web-vitals` library sending LCP/INP/CLS with attribution to your analytics, Vercel/Cloudflare/Netlify analytics.
- **Lab (diagnosis)**: Chrome DevTools Performance panel (CPU 4× slowdown, Slow 4G), Lighthouse, WebPageTest (filmstrip, waterfall, real devices), `chrome-devtools` MCP performance traces.
- **Backend**: `Server-Timing` headers, APM/tracing (OpenTelemetry, Sentry performance), DB slow query logs, `EXPLAIN ANALYZE`.
- **Bundles**: `@next/bundle-analyzer`, `vite-bundle-visualizer`/`rollup-plugin-visualizer`, `source-map-explorer`, bundlephobia/pkg-size before adding a dependency.

## 2. LCP (largest contentful paint)

Break LCP into: TTFB → resource load delay → resource load time → render delay. Fix the biggest part.
- TTFB: static generation/ISR/edge caching for public pages; fast DB queries; avoid server waterfalls; region close to users and DB.
- Load delay: the LCP image must be discoverable in the initial HTML (not CSS background set by JS, not client-fetched). `<link rel="preload">` or `fetchpriority="high"` on it; never `loading="lazy"` on it.
- Load time: AVIF/WebP, responsive `srcset`/`sizes`, compress (quality ~60–75), dimensions matching display size, CDN.
- Render delay: no render-blocking CSS/JS beyond critical; fonts with `font-display: swap`; avoid client-side hydration gating the hero.
- Hero video: poster image as LCP, video lazy.

## 3. INP (interaction responsiveness)

- Find slow interactions in field data (web-vitals attribution) or DevTools "Interactions" track.
- Long tasks (> 50ms): split work (`scheduler.yield()`, `setTimeout` chunks), defer non-urgent updates (`startTransition`), move heavy work to Web Workers or the server.
- React: avoid re-rendering huge trees on each keystroke (state colocation, memo, selectors, React Compiler), virtualize lists, debounce filters.
- Reduce hydration cost: fewer client components, partial hydration/islands (Astro), server components.
- Third-party scripts often block the main thread: defer or remove.
- Give immediate visual feedback (pressed state, optimistic UI) while work continues.

## 4. CLS (layout stability)

- Width/height or `aspect-ratio` on images, videos, iframes, embeds, ad slots.
- Fonts: metric-matched fallbacks (`size-adjust`, `ascent-override`; `next/font` does it), preload main font, limit font files.
- Don't insert content above existing content (banners, cookie bars) without reserved space; use overlays or reserve the slot.
- Skeletons with the same dimensions as final content.
- Animate with `transform`, not layout properties.

## 5. Images

- Framework image component (`next/image`, Astro `<Image>`, Nuxt Image) or an image CDN (Cloudflare Images, imgix, Cloudinary).
- Formats: AVIF → WebP → JPEG fallback; SVG for icons/logos (optimized with SVGO); PNG only when needed.
- Sizes: never serve a 4000px photo into a 400px slot; `sizes` attribute correct.
- Lazy-load below the fold (`loading="lazy"`, `decoding="async"`); eager + high priority for LCP.
- Source images in the repo > 300–500 KB are a smell (`perf_budget.py` flags).

## 6. Fonts

- Self-host (or framework font optimization); WOFF2 only; subset to used scripts (Arabic + Latin), `unicode-range` splitting.
- ≤ 2 families, ≤ 4 files on first load; variable fonts to replace multiple weights.
- `font-display: swap` + preload the 1–2 critical files + fallback metric overrides.
- Arabic fonts are large: subset aggressively; consider system fallback for body text on low-end devices if the brand allows.

## 7. JavaScript and CSS

- Server-render content; keep client components to interactive leaves.
- Route-level code splitting (default in Next/Vite routers); `dynamic()`/`React.lazy` for heavy widgets (charts, editors, maps, video players) loaded on interaction or visibility.
- Replace heavy libraries: moment → `date-fns`/`Intl`/Temporal; lodash full → native or `lodash-es` per-function; jQuery in React apps → remove; big icon packs → per-icon imports; chart libs → lighter alternatives or server-rendered SVG.
- Tree-shaking: ESM imports, `sideEffects: false` where true, avoid barrel files that pull everything (or use `optimizePackageImports` in Next.js).
- Polyfills: target modern browsers (browserslist), no blanket polyfill bundles.
- CSS: Tailwind purges by default; avoid large unused CSS frameworks; critical CSS inlined by the framework.

## 8. Backend and data

- Database: indexes for hot queries, no N+1, pagination, select only needed columns (`data-design`).
- Cache: per-request memoization, data cache (Next.js fetch cache/`unstable_cache`, Redis/Upstash) with tags, CDN caching for public responses (`s-maxage`, `stale-while-revalidate`).
- Parallelize independent awaits (`Promise.all`); stream slow sections (`<Suspense>`).
- Co-locate compute and database regions; connection pooling for serverless (Supabase pooler, Neon pooler, Prisma Accelerate/Data Proxy).
- Compression (Brotli/gzip) and HTTP/2/3 at the CDN.
- Background jobs for slow work (emails, images, AI, exports).

## 9. Rendering strategies

| Page type | Strategy |
|-----------|----------|
| Marketing, blog, docs | Static (SSG) or ISR; islands for interactivity (Astro) |
| Product catalog | ISR / cache with revalidation on change |
| Personalized dashboard | SSR with streaming, or CSR shell + cached data; skeletons |
| Highly interactive app (editor) | CSR with code splitting; server for data |
| Search results | SSR (SEO) with cached data |

## 10. Third parties

- Inventory every script (analytics, tag managers, chat, A/B testing, ads, embeds); remove unused ones.
- Load after consent and after the page is interactive (`next/script strategy="lazyOnload"`, Partytown for heavy tags).
- Facades for embeds (YouTube/Maps/chat widgets): static preview, real embed on click.
- Self-host analytics scripts where allowed; server-side tracking for critical events.

## 11. Mobile apps

- Cold start: defer non-critical initialization, lazy-load screens, avoid large synchronous storage reads at launch, Hermes on RN, baseline profiles on Android.
- Frame rate: 60fps (120 on ProMotion); use FlashList/LazyColumn/List; images sized and cached (expo-image, Coil, Nuki/Kingfisher); animations on UI thread.
- Network: cache responses, batch requests, compress images, offline-first for core data.
- Bundle/app size: remove unused assets and dependencies, App Thinning/Android App Bundles.
- Measure: Xcode Instruments, Android Studio profiler, Flipper/React Native DevTools, Firebase Performance / Sentry mobile.

## 12. Budgets and CI

Example budgets (adjust per product):
```
route JS (gzip): marketing ≤ 120 KB, app ≤ 250 KB
total CSS (gzip): ≤ 50 KB
largest image in repo: ≤ 300 KB (photos via CDN)
fonts on first load: ≤ 4 files, ≤ 150 KB total
LCP (lab, mobile): ≤ 2.5 s · CLS ≤ 0.05 · TBT ≤ 200 ms
```
- `perf_budget.py . --build-dir .next --js-budget 250 --css-budget 50` after `npm run build` in CI.
- Lighthouse CI (`@lhci/cli`) with assertions on key URLs of the preview deployment.
- Track bundle size over time (size-limit, bundlewatch, Next.js build output in PR comments).

## 13. Framework notes

- **Next.js**: server components by default; `next/image`, `next/font`, `next/script`; `generateStaticParams` + ISR; `optimizePackageImports`; check build output route sizes; avoid `"use client"` at layout level.
- **Astro**: zero JS by default; `client:visible`/`client:idle` for islands.
- **Vite SPA**: route-level lazy loading, prefetch on hover, `build.rollupOptions.output.manualChunks` only when measured.
- **Nuxt/SvelteKit**: similar: SSR/SSG, lazy components, image modules.
