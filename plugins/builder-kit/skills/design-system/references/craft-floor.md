# Craft floor

Read before any UI edit. The brief and the chosen direction override anything here except lines marked **Ban**. `design_lint.py` checks the mechanical items automatically; the rest need your eyes on the rendered result.

## 1. Verify on the render (batch these into one look per round)

- **Contrast**: body/placeholder ≥ 4.5:1, large text ≥ 3:1, UI boundaries and focus rings ≥ 3:1. Secondary text on colored surfaces tinted from that surface, not gray.
- **Hierarchy**: squint test passes; one primary action per view; headings stand out by size/weight, not only color.
- **Spacing**: on the scale; tight inside groups, generous between; more space above headings than below.
- **Alignment**: few shared edges; nothing off by 1–3px; icons optically centered with text.
- **Type**: body measure 60–75ch (Arabic ~50–70), line height per `typography.md`, no orphans in headings (`text-wrap: balance`), real copy at every breakpoint without overflow.
- **States**: hover, focus-visible, active, disabled, loading, empty, error, success, no-permission all exist and were seen.
- **Responsive**: 320/375/768/1280 without horizontal scroll; touch targets ≥ 44pt on mobile; thumb-reachable primary actions.
- **RTL**: layout mirrors, directional icons flip, numbers/media don't, Arabic font loads, no clipped diacritics.
- **Dark**: every surface, border, chart and image works; elevation by lighter surfaces.
- **Browser surfaces**: text `::selection`, `caret-color`, `accent-color` on native controls, focus ring, scrollbar (`scrollbar-color`), link underline offset, tabular numerals in tables — themed from tokens. Unthemed defaults are the cheapest tell of an assembled page.
- **Depth**: shadows have offset and blur, consistent light direction; borders or shadows, not both heavy.
- **Motion**: purposeful, ease-out, reduced-motion variant, content visible without JS.
- **Copy**: product's own words; buttons are verbs; errors say what and how to fix.
- **Coverage**: every requirement in the brief is present and findable within seconds.
- **Performance feel**: no layout shift on load (image dimensions, font fallback metrics), interactions respond < 100ms.

## 2. Bans (no brief earns these back)

- **Ban**: removing focus outlines without a visible replacement.
- **Ban**: text below 12px; body text below 16px on mobile inputs.
- **Ban**: placeholder used as the only label.
- **Ban**: disabling zoom (`user-scalable=no`, `maximum-scale=1`).
- **Ban**: emoji or Unicode symbols as the icon system.
- **Ban**: gradient-filled text for headings or body.
- **Ban**: meaning carried by color alone.
- **Ban**: lorem ipsum or "John Doe" content in a shipped screen.
- **Ban**: an eyebrow/kicker label over every section heading as decoration (a real category label that carries information is fine).
- **Ban**: auto-playing motion > 5s without pause, flashing > 3/s.
- **Ban**: nested cards.

## 3. Generic-AI defaults to refuse (unless the brief asks for them)

These are what an undecided model produces. Spotting one means an axis wasn't decided: rewrite the element, don't soften it.

Page structure:
- Hero with centered headline + purple/indigo/pink gradient + "glow" blob background.
- Three (or six) identical cards of icon + heading + two lines as the main content.
- Big-number hero metrics strip ("10x faster · 99.9% uptime · 24/7") with no source.
- Section numbers 01/02/03 when the order carries no information.
- Testimonials with stock avatars and generic praise.
- Every section fading/sliding up identically on scroll.
- A modal for something that should be a page or inline.

Surface habits:
- Glassmorphism on flat backgrounds (blur with nothing behind it).
- Colored thick `border-left` accents on cards/alerts as decoration.
- Zero-offset colored glow shadows as "depth".
- Hard offset block shadows outside a deliberately neo-brutalist world.
- Monospace as a "techy" costume for non-code text.
- Rounded-2xl everything with the same soft shadow regardless of hierarchy.
- System display fonts (Arial, Impact, default sans) as the brand's headline voice when a real face was warranted.
- Sparkles ✨ and rocket 🚀 as decoration.
- Light vs dark chosen by product category instead of the use scene.
- Copy like "Unlock the power of…", "Revolutionize your workflow", "Seamless", "Elevate".

## 4. What good looks like

- You can describe the direction in one sentence and every screen obeys it.
- A screenshot without the logo still feels like this product.
- Tokens only; no one-off values.
- The hardest states (errors, empty, long Arabic text, 1,000 rows) look as considered as the happy path.
- When torn between refined-safe and committed, commit — within the surface mode's ambition.
