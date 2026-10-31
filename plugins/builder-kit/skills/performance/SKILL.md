---
name: performance
description: Make websites, web apps, APIs and mobile apps fast and keep them fast - Core Web Vitals (LCP, INP, CLS) with field data, images and fonts, JavaScript weight and code splitting, rendering strategy (static, ISR, SSR, streaming, islands), caching and CDN, server and database latency, third-party scripts, mobile startup time and frame rate, and performance budgets enforced in CI. Use when a page or app is slow, scores badly in Lighthouse/PageSpeed, before launch, when adding heavy dependencies, images or third-party scripts, or when the user says performance, slow, speed, Core Web Vitals, Lighthouse, bundle size, الأداء, الموقع بطيء, سرعة التطبيق. Ships perf_budget.py (built JS/CSS sizes with gzip, largest chunks, heavy dependencies, oversized images and fonts).
---

# Performance

Speed is a feature users feel before they read a word: slow pages lose conversions, rankings and patience. Most slowness in AI-built apps comes from a few repeat causes: unoptimized hero images, too much client JavaScript, render-blocking fonts and third parties, data waterfalls, and missing database indexes. Measure, fix the biggest cause, measure again, then lock the gain with a budget.

| File | Use it for |
|------|-----------|
| `references/playbook.md` | Targets, measuring (field vs lab), LCP/INP/CLS fixes, images, fonts, JS and CSS, rendering strategies, caching/CDN, backend and DB, third parties, mobile apps, budgets and CI, framework notes |
| `scripts/perf_budget.py` | After a build: total and largest JS/CSS (raw + gzip) vs budgets, heavy dependencies in `package.json`, images and fonts over size limits in source/public |

## 1. Targets (75th percentile of real users, mobile)

| Metric | Good | Meaning |
|--------|------|---------|
| LCP (Largest Contentful Paint) | ≤ 2.5 s | main content visible |
| INP (Interaction to Next Paint) | ≤ 200 ms | responds to taps/clicks |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | nothing jumps |
| TTFB | ≤ 0.8 s | server responds |
| API p95 | per spec (e.g. ≤ 300 ms reads) | backend speed |
| Client JS on a route | ≤ ~170 KB gzip for content/marketing pages; justify more for apps | download + parse + execute on mid-range phones |
| Mobile cold start | ≤ 2 s to first usable screen | app launch |

## 2. Rules

1. **Measure before and after**: field data (CrUX/PageSpeed Insights, Vercel Speed Insights, web-vitals library to your analytics) beats lab; use lab (Lighthouse, WebPageTest, DevTools with CPU 4× + slow 4G) to diagnose.
2. **The LCP element is sacred**: server-rendered in the HTML, image optimized (AVIF/WebP, right size, `fetchpriority="high"`, no lazy-load), no client-side fetch before it appears.
3. **Ship less JavaScript**: server components/islands, code-split per route, lazy-load heavy widgets, no full-library imports, avoid client-side rendering for content.
4. **Reserve space** for every image, video, embed, ad and late component (width/height or `aspect-ratio`) and load fonts with metric-matched fallbacks.
5. **Keep the main thread free**: break long tasks, debounce input work, move heavy computation to the server or a worker, virtualize long lists.
6. **Cache at every layer**: CDN for static and cacheable pages (immutable hashed assets for a year), HTTP caching headers, data caching with explicit invalidation, database indexes.
7. **Third parties are guilty until proven innocent**: load analytics/chat/ads after interaction or idle, via a facade, or server-side; remove what nobody uses.
8. **Budgets in CI**: `perf_budget.py` after build and Lighthouse CI on key pages; a PR that breaks the budget explains why or fixes it.

## 3. Workflow: slow page or app

1. Get numbers: PageSpeed Insights for the URL (field + lab), DevTools Performance trace on a throttled profile, server timing for API calls.
2. Identify the bottleneck by metric: LCP (`playbook.md` §2), INP (§3), CLS (§4), TTFB/API (§8).
3. Fix the biggest one; re-measure; repeat.
4. Run `python3 <skill>/scripts/perf_budget.py . --build-dir <dir>`; set budgets in the project's `CLAUDE.md`/CI.

## 4. Done when

- [ ] Field or lab LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 on mobile for key pages.
- [ ] `perf_budget.py` within budgets (or exceptions documented); no heavy dependency without a reason.
- [ ] LCP image optimized and prioritized; fonts self-hosted with swap + fallback metrics; layout space reserved.
- [ ] Third-party scripts deferred or removed; caching headers correct; slow queries indexed.
- [ ] Budgets enforced in CI; Web Vitals reported from real users.
