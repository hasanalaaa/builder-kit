# Typography

Type carries most of a UI. Good type with plain layout beats fancy layout with default type.

## 1. Scale

Pick a ratio by surface:
| Surface | Base | Ratio | Notes |
|---------|------|-------|-------|
| Dense tool | 14px | 1.125–1.2 | Many sizes close together; rely on weight and color for hierarchy |
| Product UI | 16px | 1.2–1.25 | Default |
| Content / docs | 17–18px | 1.25 | Reading comfort |
| Marketing / brand | 16–18px body | 1.333–1.5 for display | Big contrast between display and body |

Product UI scale (px): 12 · 14 · 16 · 18 · 20 · 24 · 30 · 36 · 48 · 60 · 72. Use ≤ 6 sizes on one screen.

Fluid display type (marketing): `font-size: clamp(2.5rem, 1.5rem + 4vw, 5rem)`. Keep body fixed (16–18px); never fluid body text below 16px.

Minimums: 16px for body on mobile (also prevents iOS zoom on input focus), 12px absolute floor for captions/labels (`design_lint.py` errors below 12px). Display tops out around 6rem on most screens.

## 2. Line height, measure, spacing

| Text | Line height | Notes |
|------|------------|-------|
| Display (≥ 36px) | 1.0–1.15 | Tighten as size grows |
| Headings (20–30px) | 1.2–1.3 | |
| Body Latin | 1.5–1.65 | |
| Body Arabic | 1.7–1.9 | Arabic has tall ascenders/descenders and diacritics; it needs more |
| UI labels, buttons | 1.2–1.4 | Single line |

- Measure: 60–75 characters per line for Latin body; ~50–70 for Arabic (`max-width: 68ch` on prose).
- Letter-spacing: tighten large Latin display (−0.01 to −0.03em, never below −0.04em), loosen small caps/uppercase labels (+0.04 to +0.08em). **Never add letter-spacing to Arabic**: it breaks the connected script.
- Paragraph spacing ≈ 0.75–1× line height. Space above a heading > space below it (it belongs to what follows).
- `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs.
- Left-align (start-align) body text. Center only short blocks (≤ 3 lines).

## 3. Weights and styles

- Two weights per family usually suffice (regular 400 + semibold 600; add bold 700 for display if needed).
- Hierarchy order of tools: size → weight → color → case → spacing. Don't stack all of them.
- Avoid all-caps for anything longer than a short label; never in Arabic (no case).
- Italic: Latin emphasis only. Arabic has no true italic; emphasize with weight or color, never synthetic slant.

## 4. Pairing

- One family for UI is enough; a second for display or editorial voice. Max three including mono.
- Pair by contrast with a shared trait: serif display + grotesk body; humanist sans + monospace for data.
- Variable fonts: one file, all weights, smaller total bytes.
- Use `font-variant-numeric: tabular-nums` for tables, prices, timers, counters.
- `data/fonts.csv` has curated pairings (Latin + Arabic) with mood and use; search it: `design_search.py "<mood>" --domain fonts`.

## 5. Arabic typography

**Choosing Arabic fonts** (all on Google Fonts unless noted):
| Font | Style | Use |
|------|-------|-----|
| IBM Plex Sans Arabic | Clean, neutral, many weights | Product UI, enterprise, bilingual with IBM Plex Sans |
| Noto Sans Arabic / Noto Kufi Arabic / Noto Naskh Arabic | Broad coverage, neutral | UI (Sans), headings (Kufi), long reading (Naskh) |
| Tajawal | Light geometric sans | Modern consumer apps, Gulf brands |
| Cairo | Geometric, wide, strong | Headlines, marketing, apps |
| Almarai | Friendly, readable | Consumer apps, body text |
| Readex Pro | Modern variable, good Latin pair | Tech products, bilingual UI |
| Alexandria | Geometric variable, many weights | Modern brands, headings |
| Rubik | Rounded, has Arabic | Friendly apps, education |
| Vazirmatn | Neutral, variable | UI, Persian/Arabic |
| Noto Naskh Arabic, Amiri, Scheherazade New, Markazi Text | Naskh (book) style | Long reading, editorial, religious and literary content |
| Reem Kufi, El Messiri, Changa, Lalezar, Marhey, Rakkas, Aref Ruqaa | Display/expressive | Headlines and brand moments only |

**Rules**
- Arabic at the same font-size looks smaller than Latin. Bump Arabic body 1–2px (or ~10–15%) or pick a font with a large x-height equivalent, and use line-height 1.7–1.9.
- Pair Arabic and Latin fonts with similar stroke weight and vertical metrics (IBM Plex Sans Arabic + IBM Plex Sans; Readex Pro + Inter; Noto Kufi + Noto Sans). List the Arabic font in `font-family` together with the Latin font, ordered by the page language:
  `font-family: "IBM Plex Sans Arabic", "Inter", system-ui, sans-serif;` on `:lang(ar)`, Latin first on `:lang(en)`.
- Never letter-space, never italicize, never uppercase-transform Arabic. Never break words with hyphenation.
- Keep diacritics (tashkeel) legible: check line-height doesn't clip them, especially in buttons and inputs with fixed heights.
- Numerals: decide Western Arabic (0–9) or Eastern Arabic (٠–٩) per product and audience, and be consistent. Gulf commercial apps mostly use 0–9; formal/government content may use ٠–٩. Use `Intl.NumberFormat('ar-…', { numberingSystem })` to control it.
- Mixed text: wrap embedded Latin/numbers in `<bdi>` or use `unicode-bidi: isolate` where order breaks (phone numbers, codes, emails).
- Subset fonts to Arabic + Latin ranges you use; Arabic fonts are large.

## 6. Font loading

- Self-host (or `next/font`), `font-display: swap`, preload the 1–2 files used above the fold, subset by `unicode-range`.
- Set a fallback with matching metrics (`size-adjust`, `ascent-override`; `next/font` does this) to avoid layout shift.
- Max ~4 font files on first load. Every extra weight costs.

## 7. Common defects

- Too many sizes (> 8 on a page), sizes not on the scale.
- Gray body text below 4.5:1 "for elegance".
- Line length > 90ch on desktop.
- Centered paragraphs.
- Headline in a system font (Arial/Impact) while the brand deserves a real face.
- Arabic falling back to a system font mid-page because the Arabic family wasn't declared.
- Fixed-height containers clipping Arabic diacritics or descenders.
