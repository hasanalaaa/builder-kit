# Stacks and providers

Versions are deliberately absent: confirm the current stable release in official docs at setup time.

## 1. Default stack per project type

| Project type | Default | Change it when |
|--------------|---------|----------------|
| Marketing site, blog, docs, landing page | **Astro** (static output, islands only where interactive) + Tailwind + MDX; host on Cloudflare Pages / Netlify / Vercel | Heavy app-like interactivity → Next.js. Non-technical editors → add a headless CMS (Sanity, Payload, Storyblok) |
| SaaS / logged-in web app | **Next.js (App Router) + TypeScript strict + Tailwind + shadcn/ui**, Postgres via **Supabase** (auth + DB + storage + RLS) or Neon + Drizzle + Better Auth / Clerk; Stripe; host on Vercel | Mostly static with few app screens → Astro + API. Team knows Python → FastAPI backend + React/Vite front end. Self-hosting required → Postgres + Drizzle + Docker on a VPS/Fly/Railway |
| Internal tool / admin panel | Next.js or React + Vite + shadcn/ui on the existing DB, behind SSO | A low-code admin (Retool, Appsmith) is fine for internal-only if data stays in your DB |
| Public API / backend only | **TypeScript: Hono** (edge/serverless) or **Fastify/NestJS** (long-running). **Python: FastAPI** + pydantic + SQLAlchemy/SQLModel. Postgres. OpenAPI generated from code | Very high throughput / low latency → Go. Heavy data/ML → Python |
| Mobile app (iOS + Android) | **Expo (React Native) + TypeScript + Expo Router**, EAS Build/Submit, Supabase or your API | Platform-native UX, widgets, heavy device APIs, best performance → **SwiftUI** (iOS) / **Jetpack Compose** (Android). Team knows Dart → Flutter |
| iOS-only app | **SwiftUI + Swift Concurrency + SwiftData** (or GRDB), StoreKit 2 | Needs Android soon → Expo |
| Desktop app | **Tauri** (small, secure, Rust core + web UI) | Needs mature Node ecosystem or heavy Chromium APIs → Electron (with launch-security P2 hardening). Mac-only → SwiftUI |
| Browser extension | **WXT** (or Plasmo) + TypeScript, Manifest V3 | — |
| E-commerce | **Shopify** (hosted, or headless with Hydrogen) for standard stores | Custom marketplace/multi-vendor logic → Next.js + Stripe Connect + Postgres; Medusa if you need open-source commerce |
| Realtime / collaborative | Next.js + Supabase Realtime, or Liveblocks / PartyKit / Yjs for multiplayer editing | Massive fan-out → dedicated pub/sub (Ably, Pusher) |
| AI app (chat, agents, RAG) | Next.js + **Vercel AI SDK** or direct provider SDK (Anthropic/OpenAI) on the server; Postgres + **pgvector** for embeddings; background jobs for long work | Python-heavy pipelines → FastAPI service. Large vector scale → dedicated vector DB |
| CLI / dev tool | TypeScript (Node, `commander`) or Python (`typer`) or Go (single binary) | — |
| Game (web) | Phaser / PixiJS / Three.js (+ React Three Fiber) | Native/console → Godot / Unity |

## 2. Providers (commodities to buy)

| Need | Default | Alternatives / notes |
|------|---------|----------------------|
| Database | **Postgres** (Supabase, Neon, RDS) | SQLite/Turso for local-first or tiny apps. Avoid document DBs for relational data |
| ORM / query | **Drizzle** (TS) or Prisma; SQLAlchemy/SQLModel (Python) | Supabase client + RLS when the browser talks to the DB directly |
| Auth | **Supabase Auth**, Clerk, Better Auth, Auth.js; Sign in with Apple/Google on mobile | Never roll your own password storage or sessions (launch-security 01/05/15) |
| Payments (web) | **Stripe** (Checkout + Billing + webhooks) | Paddle / Lemon Squeezy as merchant of record (they handle global sales tax). Regional gateways (e.g. Tap, HyperPay, Moyasar for Gulf cards, mada) when local cards matter |
| Payments (in-app) | **StoreKit 2 / Google Play Billing**, optionally via RevenueCat | Store rules decide, not preference (launch-security S1–S2) |
| Email (transactional) | **Resend**, Postmark, AWS SES | Never send from a personal mailbox. SPF/DKIM/DMARC (email-notifications) |
| Push notifications | Expo Notifications / FCM / APNs; OneSignal | — |
| File storage | **S3-compatible**: Supabase Storage, Cloudflare R2, S3 | Private by default, signed URLs (launch-security 18) |
| Images | Next/Image, Cloudflare Images, imgix | Always serve modern formats and sizes (performance) |
| Search | Postgres full-text → Meilisearch / Typesense → Algolia | Start with Postgres |
| Background jobs / cron | Inngest, Trigger.dev, Supabase cron + Edge Functions, Cloud Tasks; BullMQ/Celery when self-hosting | — |
| Error tracking | **Sentry** | — |
| Logs / metrics | Provider logs + Axiom / Better Stack / Grafana Cloud | observability skill |
| Product analytics | PostHog (also flags + session replay), Plausible for privacy-first page analytics | Consent rules (legal-compliance) |
| Feature flags | PostHog, Unleash, GrowthBook, or a DB table | — |
| CMS | Sanity, Payload, Storyblok, Contentful | MDX in repo for developer-written content |
| Hosting | **Vercel** (Next.js), **Cloudflare** (static, Workers), Netlify; **Fly.io / Railway / Render** for long-running servers and workers | VPS + Docker + Caddy when cost or control matters |
| DNS / CDN / WAF | **Cloudflare** | — |
| Maps | Mapbox, Google Maps, MapLibre + free tiles | — |
| AI models | Anthropic (Claude), OpenAI, Google; via server only | ai-features skill: cost caps, fallbacks, evals |
| i18n | next-intl (Next.js), i18next/react-i18next, Expo Localization + i18next | i18n-rtl skill |
| Forms | React Hook Form + Zod; TanStack Form | — |
| Server state | TanStack Query; framework data loading (RSC, loaders) first | — |
| Client state | Framework/state primitives first; Zustand when shared global state is real | — |
| Testing | Vitest + Testing Library, Playwright (E2E), pytest + httpx | testing-strategy skill |

## 3. Decision table template (for the ADR)

| Concern | Choice | Why (spec link) | Rejected | Exit plan |
|---------|--------|-----------------|----------|-----------|
| Front end | | | | |
| Backend / API | | | | |
| Database | | | | |
| Auth | | | | |
| Payments | | | | |
| Hosting | | | | |
| Email | | | | |
| Storage | | | | |
| Observability | | | | |
| AI | | | | |

Cost estimate: launch <$/month>, 10× users <$/month>. Spend caps set on: <providers>.

## 4. Migration notes

- Migrate one boundary at a time behind an interface you already have (data access module, auth helper). Never big-bang.
- Dual-write or backfill data with a reversible migration; verify counts and checksums before switching reads.
- Keep the old provider in read-only mode until the new one has run a full billing/usage cycle.
- Lovable/Bolt/v0 exports: they are usually Vite/Next + Supabase. Keep the stack, fix the structure (project-rescue).
