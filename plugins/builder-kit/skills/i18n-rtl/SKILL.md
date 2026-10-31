---
name: i18n-rtl
description: Load whenever an app has Arabic or any second language, or a layout must flip. lang/dir, logical CSS and Tailwind ms/me/ps/pe, icon mirroring, bidi isolation, ICU plurals, locale dates/numbers/Hijri, Arabic search. Triggers: RTL, عربي, دعم العربية, ترجمة.
---

# i18n and RTL

Arabic is not "English flipped". It needs the right direction model, fonts with proper size and line height (`design-system/references/typography.md` §5), correct plurals, numerals the audience expects, natively written copy, and search that understands Arabic spelling variants. Build it in from the first component; retrofitting RTL into a physical-property codebase means touching every file.

| File | Use it for |
|------|-----------|
| `references/rtl-and-i18n.md` | Direction setup per stack, logical properties table, mirroring rules, bidi, message catalogs and ICU, plurals and gender, formatting (dates, numbers, currency, Hijri), Arabic search normalization, locale routing and SEO, store listings, testing |
| `scripts/rtl_lint.py` | Flag physical CSS properties, Tailwind `ml-/mr-/pl-/pr-/left-/right-/text-left/rounded-l…`, React Native `marginLeft/paddingRight/left/right`, missing `lang`/`dir` on `<html>`, directional icons without RTL flip, `toLocaleString()`/`Intl` without locale, hard-coded JSX strings when an i18n library is installed |

## 1. Rules

1. **Direction at the root**: `<html lang="ar" dir="rtl">` (from the active locale), `I18nManager` (RN), `Directionality`/`locale` (Flutter), `\.environment(\.layoutDirection, .rightToLeft)` follows the system on iOS. Components never hard-code direction.
2. **Logical properties only** in shared code: `margin-inline-start`, `inset-inline-end`, `text-align: start`, Tailwind `ms-* me-* ps-* pe-* start-* end-* text-start rounded-s border-e`, RN `marginStart/paddingEnd/start/end`. Physical left/right only when it's truly physical (a shadow direction, a map overlay).
3. **Mirror what has direction**: arrows, chevrons, back/next, progress, sliders, carousels, breadcrumbs, timelines, drawers, swipe actions. **Don't mirror**: play/media controls, clocks, logos, checkmarks, numbers, phone numbers, code, charts' numeric axes (decide and keep consistent).
4. **Isolate mixed-direction runs**: numbers with units, phone numbers, emails, URLs, order codes, Latin product names inside Arabic sentences → `<bdi>` or `unicode-bidi: isolate`, `dir="ltr"` on inputs for email/phone/URL/code.
5. **No strings in code.** All user-facing text in message catalogs keyed by meaning (`invoice.sendButton`), with ICU MessageFormat for plurals, gender and variables. Never concatenate translated fragments.
6. **Arabic plurals have six forms** (`zero, one, two, few, many, other`). Every countable message uses ICU plural syntax.
7. **Format with `Intl`/platform APIs and an explicit locale**: dates, times, numbers, currency, percentages, lists, relative time. Decide Western (0–9) vs Arabic-Indic (٠–٩) digits per product (`-u-nu-latn` / `-u-nu-arab`) and keep it consistent.
8. **Locale is user-controlled and persisted**; default from the browser/OS (`Accept-Language`, device locale); URL-based locale for public pages (`/ar/...`, `/en/...`) for SEO with `hreflang`.
9. **Copy is written natively** per language (register, gender handling, tone): `design-system/references/ux-copy.md` §4. Machine translation is a draft, reviewed by a native speaker for public text.
10. **Test both directions on every UI change**: screenshot/E2E in `ar` and `en`, pseudo-localization for length, `rtl_lint.py` 0 ERROR.

## 2. Workflow: new project

1. Choose the i18n library for the stack (`rtl-and-i18n.md` §4): next-intl, i18next/react-i18next, vue-i18n, Paraglide, `expo-localization` + i18next, Flutter `intl`/ARB, iOS String Catalogs, Android `strings.xml`.
2. Set up locales (`ar` default or `en` default per spec), routing, `lang`/`dir` on the root, fonts per locale, `Intl` helpers in one module (`lib/format.ts`).
3. Add `rtl_lint.py` and an RTL E2E project to CI.

## 3. Workflow: retrofitting RTL into an existing app

1. Run `rtl_lint.py .` to inventory physical properties and hard-coded strings.
2. Set `dir` at the root from the locale; look at every screen in RTL; list breakages.
3. Replace physical properties with logical ones file by file (mechanical; Tailwind: `ml-`→`ms-`, `mr-`→`me-`, `pl-`→`ps-`, `pr-`→`pe-`, `left-`→`start-`, `right-`→`end-`, `text-left`→`text-start`, `rounded-l`→`rounded-s`, `border-l`→`border-s`).
4. Flip directional icons (`rtl:-scale-x-100` or a mirrored icon).
5. Extract strings to catalogs; add Arabic translations with plurals.
6. Verify with screenshots in both directions.

## 4. Done when

- [ ] `rtl_lint.py` 0 ERROR; remaining WARNs justified.
- [ ] Every screen checked in `ar` (RTL) and `en`, on mobile and desktop.
- [ ] All user-facing strings in catalogs; plurals via ICU; no concatenation.
- [ ] Dates/numbers/currency formatted via `Intl` with explicit locale and the chosen digit system.
- [ ] Mixed-direction content isolated; email/phone/code inputs `dir="ltr"`.
- [ ] Arabic font loaded with correct size/line height; no clipped diacritics.
- [ ] Locale switch persists; public pages have localized URLs, `hreflang` and translated metadata.
