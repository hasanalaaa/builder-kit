# Color

## 1. Work in OKLCH

OKLCH (`oklch(L C H)`) is perceptually uniform: equal steps in L look equal, so scales are even and contrast is predictable. All modern browsers support it. Hex stays for brand docs; tokens use OKLCH.

- **L** lightness 0–1 · **C** chroma 0–~0.37 (how colorful) · **H** hue 0–360.
- A scale is one hue with L stepping down and C peaking in the middle (very light and very dark colors can't hold much chroma).
- `palette.py` builds 11-step scales (50…950) this way and clamps to the sRGB gamut.

## 2. Building a palette

1. **Brand color** → the primary scale. Usually the brand hex lands near step 500–600.
2. **Neutrals**: a gray scale tinted 1–2% toward the brand hue (C ≈ 0.005–0.015). Pure gray looks dead next to a colored brand.
3. **Semantic**: success (green ~145), warning (amber ~75), danger (red ~25), info (blue ~250). Adjust hues so none collides with the brand (a red brand needs a distinct danger treatment: icon + text, not color alone).
4. **Accent** (optional): one complementary or analogous hue for highlights and charts. Most products need zero or one accent.

Proportion: ~60% neutral surfaces, ~30% secondary surfaces/text, ~10% brand + accent. Color that appears everywhere stops meaning anything.

## 3. Mapping scales to semantic tokens (light)

| Token | Typical step |
|-------|-------------|
| background | neutral-50 (or white) |
| foreground | neutral-950/900 |
| muted | neutral-100 · muted-foreground neutral-600 (must pass 4.5:1 on background) |
| border / input | neutral-200 / neutral-300 |
| primary | brand-600 (adjusted until white or dark text passes 4.5:1) |
| primary-foreground | white or brand-950, whichever passes |
| accent (hover/selected) | brand-50/100 · accent-foreground brand-900 |
| ring | brand-500 (≥ 3:1 against background) |
| destructive | red-600 · foreground white |

Dark: background neutral-950 tinted, card neutral-900, foreground neutral-50, muted-foreground neutral-400, border neutral-800, primary brand-400/500 (lighter so it reads on dark), and re-check every pair.

## 4. Contrast requirements

WCAG 2.2 AA (the legal baseline in most places):
| Content | Minimum ratio |
|---------|---------------|
| Body text (< 24px, or < 18.66px bold) | 4.5:1 |
| Large text (≥ 24px, or ≥ 18.66px bold) | 3:1 |
| UI component boundaries, focus indicators, icons that carry meaning, chart elements | 3:1 against adjacent colors |
| Disabled controls, pure decoration, logos | exempt (still keep disabled legible) |
| Placeholder text | treat as text: 4.5:1 (or don't rely on placeholders as labels) |

APCA (the candidate model for WCAG 3, better for dark mode and thin fonts), as a second opinion: |Lc| ≥ 75 body text, ≥ 60 for content text at larger sizes, ≥ 45 for large headings, ≥ 30 for non-text UI. `contrast.py` reports both. Ship on WCAG; use APCA to catch dark-mode and thin-weight problems WCAG misses.

## 5. Color rules

- Never convey meaning by color alone: pair with icon, text, pattern or position (errors, chart series, status pills).
- Secondary text on a colored surface is a tint of that surface's foreground, not gray.
- Links in body text: underline (or a non-color cue) plus color.
- Gradients: two to three stops in nearby hues and the same lightness band; never as text fill; one gradient moment per page at most.
- Avoid the default AI palette: purple→indigo→pink gradients on white with glowing cards. Choose a hue from the brand, not from the template.
- Saturated colors on large areas tire eyes; save high chroma for small, important things.
- Check your palette for color-vision deficiency (protanopia/deuteranopia: red/green confusion; tritanopia: blue/yellow). Distinguish series by lightness as well as hue.

## 6. Colorize (adding color to a gray UI)

Add color only where it carries meaning:
1. **Brand moment**: primary button, active nav item, focus ring, one hero element.
2. **State**: success/warning/danger/info with icons.
3. **Category**: tags, avatars, calendar events (a fixed categorical set of 6–8 hues of equal lightness).
4. **Data**: charts (§7).
Everything else stays neutral.

## 7. Data visualization color

- Categorical: up to 6–8 hues with similar lightness and chroma; order them so adjacent series contrast; beyond 8, group into "Other".
- Sequential (one measure, low→high): one hue, lightness steps; dark = more (on light backgrounds).
- Diverging (below/above a midpoint): two hues meeting at a neutral midpoint.
- Highlight one series by muting the rest to neutral, not by adding more color.
- Text labels on chart elements still need 4.5:1; chart marks need 3:1 against the background.
- Give dark-mode chart colors their own values (slightly lighter, slightly less chroma).

## 8. Fitting a brand color that fails contrast

If the brand color can't carry white text at 4.5:1:
- Use a darker step of the same hue for buttons (brand-700) and keep the exact brand color for large graphics and logos.
- Or use dark text on the brand color.
- Never lighten text to "match the brand" below contrast.

## 9. Palette moods (seeds for `palette.py --hue`)

| Mood | Hue (OKLCH) | Chroma | Notes |
|------|------------|--------|-------|
| Trust / finance / enterprise | 240–260 blue | 0.12–0.18 | Most common; differentiate with neutrals and type |
| Growth / health / sustainability | 145–165 green | 0.10–0.16 | Avoid confusing with success state: add a distinct success hue or icon |
| Energy / food / youth | 30–60 orange | 0.15–0.20 | Check contrast; often needs dark text |
| Luxury / calm | 280–310 violet or neutral + gold 80–90 | 0.05–0.12 | Low chroma reads premium |
| Gulf heritage | deep green 160, sand 80, indigo 270 | 0.06–0.14 | Pair with Arabic display type |
| Technical / dev | 190–210 cyan/teal on dark | 0.10–0.15 | Dark mode first |
| Playful / kids | multiple hues 30, 90, 200, 330 | 0.14–0.20 | Keep text on neutrals |
| Health / medical | 200–230 calm blue, 170 teal | 0.08–0.12 | Avoid alarming reds outside real alerts |
