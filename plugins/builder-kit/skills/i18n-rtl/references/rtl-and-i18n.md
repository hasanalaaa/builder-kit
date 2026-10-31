# RTL and i18n reference

## 1. Direction setup

**Next.js (App Router + next-intl)**
```tsx
// app/[locale]/layout.tsx
export default async function LocaleLayout({ children, params }) {
  const { locale } = await params;
  const dir = ["ar", "he", "fa", "ur"].includes(locale) ? "rtl" : "ltr";
  return <html lang={locale} dir={dir}><body className={locale === "ar" ? arabicFont.className : latinFont.className}>{children}</body></html>;
}
```
**Vite/React SPA**: set `document.documentElement.lang/dir` when the locale changes (i18next `languageChanged` event).
**Tailwind**: v3.3+ and v4 have logical utilities (`ms-`, `me-`, `ps-`, `pe-`, `start-`, `end-`, `text-start`, `rounded-s/e`, `border-s/e`) and `rtl:`/`ltr:` variants.
**React Native**: `I18nManager.allowRTL(true)`; `I18nManager.forceRTL(isRTL)` then reload (`Updates.reloadAsync()`) — direction changes require a restart. Use `start`/`end` style props. Expo: `expo-localization` `getLocales()[0].textDirection`; set `"supportsRTL": true` in app config (`extra` / `expo-localization` plugin).
**Flutter**: `MaterialApp(locale:, supportedLocales:, localizationsDelegates:)`; `Directionality` follows the locale; use `EdgeInsetsDirectional`, `AlignmentDirectional`, `PositionedDirectional`.
**SwiftUI**: leading/trailing everywhere; mirrored SF Symbols automatic; test with the "Right-to-Left Pseudolanguage" scheme option.
**Android**: `android:supportsRtl="true"`, `start/end` attributes, `autoMirrored="true"` on directional vector drawables.

## 2. Logical properties

| Physical | Logical CSS | Tailwind | React Native |
|----------|-------------|----------|--------------|
| margin-left / right | margin-inline-start / end | ms- / me- | marginStart / marginEnd |
| padding-left / right | padding-inline-start / end | ps- / pe- | paddingStart / paddingEnd |
| left / right | inset-inline-start / end | start- / end- | start / end |
| text-align: left / right | text-align: start / end | text-start / text-end | textAlign: 'auto' (follows direction) |
| border-left / right | border-inline-start / end | border-s / border-e | borderStartWidth / borderEndWidth |
| border-top-left-radius | border-start-start-radius | rounded-ss / rounded-s | borderTopStartRadius |
| float: left / right | float: inline-start / inline-end | float-start / float-end | — |
| translateX(10px) | flip with `[dir=rtl] &` or `rtl:` | rtl:-translate-x-… | conditional on `I18nManager.isRTL` |

Flexbox and grid follow direction automatically (`flex-direction: row` starts at the inline start); `space-x-*` in Tailwind needs `rtl:space-x-reverse` on older versions — prefer `gap-*`.

## 3. Mirroring

Mirror (flip horizontally in RTL): back/forward arrows, chevrons in lists/breadcrumbs/pagination, "send" paper-plane (debated; follow platform), undo/redo, progress bars and steppers, sliders, carousels and swipe direction, drawer/sheet side, text-alignment icons, list-with-bullet icons, reply/forward.
Don't mirror: media play/pause/rewind (they represent tape direction), clocks and circular refresh, checkmarks, logos and brand marks, maps, phone/keyboard icons, numbers, math, graphs' time axes (choose per audience and stay consistent), images of real objects.
Implementation: `className="rtl:-scale-x-100"` on directional icons; or icon components with a `mirror` prop.

## 4. Libraries

| Stack | Library | Notes |
|-------|---------|-------|
| Next.js App Router | next-intl | routing middleware, server components support, ICU |
| React (any) | i18next + react-i18next (+ i18next-icu) or FormatJS react-intl | |
| Vue / Nuxt | vue-i18n / @nuxtjs/i18n | |
| Svelte / any (compiler) | Paraglide JS | type-safe, tree-shaken messages |
| Astro | built-in i18n routing + a message lib | |
| Expo / RN | expo-localization + i18next / FormatJS | Intl polyfills on Hermes may be needed for plurals/relative time |
| Flutter | flutter_localizations + intl, ARB files | |
| iOS | String Catalogs (`.xcstrings`) | plural variants built in |
| Android | `strings.xml` + `plurals` | |
| Backend (emails, PDFs) | same catalogs on server (ICU via `intl-messageformat` / Babel / python-i18n) | |

## 5. Messages and ICU

```json
{
  "invoice": {
    "count": "{count, plural, =0 {لا توجد فواتير} one {فاتورة واحدة} two {فاتورتان} few {# فواتير} many {# فاتورة} other {# فاتورة}}",
    "sentTo": "أُرسلت الفاتورة إلى {name}",
    "greeting": "{gender, select, female {مرحبًا بكِ} male {مرحبًا بك} other {مرحبًا بك}}"
  }
}
```
- Keys by meaning, namespaced by feature. One catalog per locale per feature or a single file per locale for small apps.
- Never build sentences from pieces (`t('you have') + n + t('items')`). Word order differs.
- Provide context for translators (descriptions, screenshots); limit length only when truly constrained.
- Missing-key detection in CI (i18next-parser, next-intl's type checking, FormatJS extract).
- Pseudo-localization (`[!!! Ŝàvé çhàñĝéš !!!]` + 30–40% length) to find hard-coded strings and overflow.

## 6. Formatting

```ts
const nf = new Intl.NumberFormat("ar-SA-u-nu-latn", { style: "currency", currency: "SAR" });   // ١٢٣ vs 123: choose -u-nu-arab or -u-nu-latn
const df = new Intl.DateTimeFormat("ar-SA-u-ca-gregory", { dateStyle: "long", timeZone: userTz }); // Gregorian
const hijri = new Intl.DateTimeFormat("ar-SA-u-ca-islamic-umalqura", { dateStyle: "long" });       // Hijri (Umm al-Qura)
const rel = new Intl.RelativeTimeFormat("ar", { numeric: "auto" });                                // "أمس"
const list = new Intl.ListFormat("ar", { type: "conjunction" });                                   // "أ وب وج"
```
- Note: `ar-SA` defaults to the Islamic calendar in some engines; set `-u-ca-gregory` explicitly when you mean Gregorian.
- Currency: symbol position and spacing differ; always format with `Intl`, never `"SAR " + n`.
- Store times in UTC; format in the user's time zone. Week start differs (Saturday/Sunday/Monday) — use locale data.
- Phone numbers: store E.164; format with libphonenumber; input `dir="ltr"` and `inputmode="tel"`.
- Accept both digit systems in numeric inputs and normalize to Western digits before validation (`'٠١٢٣٤٥٦٧٨٩'` → `0–9`, and Persian `۰–۹`).

## 7. Bidi (bidirectional text)

- Wrap user-generated or variable content in `<bdi>` inside sentences: `<p>أرسل <bdi>{userName}</bdi> رسالة</p>`.
- Inputs for email, URL, code, IBAN, phone: `dir="ltr"` + `text-align: start`/`end` as designed.
- `dir="auto"` on user-generated text blocks (comments, chat messages) so each message takes its own direction.
- Neutral characters (parentheses, slashes, punctuation) at run boundaries cause most bugs; test with mixed strings like `طلب رقم (A-1024) تم`.

## 8. Arabic search and sorting

Normalize on both index and query:
- Remove diacritics (tashkeel) and tatweel (ـ).
- Unify alef forms (أ إ آ ٱ → ا), ya/alef maqsura (ى → ي), taa marbuta (ة → ه) for search, hamza on waw/ya (ؤ → و, ئ → ي).
- Normalize digits to Western.
- Postgres: a `normalize_ar(text)` SQL function used in a generated `tsvector` column (`simple` config) or `pg_trgm` for fuzzy; Meilisearch/Typesense/Algolia have Arabic support with configurable normalization.
- Sorting: `Intl.Collator('ar')` / ICU collation in the database (`COLLATE "ar-x-icu"`).

## 9. Locale routing and SEO

- Public pages: `/ar/...` and `/en/...` (or subdomains); default locale chosen by `Accept-Language` on first visit with a visible switch; remember choice in a cookie.
- `<link rel="alternate" hreflang="ar" href=...>` for each language + `x-default`; localized `<title>`, meta description, Open Graph, structured data (`seo-discoverability`).
- Translate slugs when it helps search; keep IDs stable.
- Sitemaps list all locale URLs.
- App UI behind login can use a user setting instead of URL locale.

## 10. Emails, PDFs, notifications

- Render with the recipient's locale and direction (`dir="rtl"` on the email `<html>` and table cells, `text-align: right` inline for clients that ignore `dir`).
- PDFs: an engine with Arabic shaping (Chromium/Playwright PDF, or libraries with HarfBuzz shaping); never naive PDF libs that print disconnected letters.
- Push notifications: localized server-side by stored user locale, or use platform localization keys.

## 11. Store listings and assets

- App name, subtitle, keywords, description, screenshots per locale (Arabic screenshots show RTL UI).
- Images with text: localized variants; avoid text baked into images.

## 12. Testing

- Playwright projects for `ar-SA` and `en-US`; visual snapshots of key pages in both.
- Unit tests for formatters (plurals for 0, 1, 2, 3, 11, 100; digits; currency).
- RN: test on a device/simulator with Arabic system language (direction applies after restart).
- Checklist per screen: layout mirrored, icons correct, numbers readable, no truncation, Arabic font used, inputs behave, focus order follows reading order.
