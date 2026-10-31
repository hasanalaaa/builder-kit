# Layout, spacing and hierarchy

## 1. Spacing system

- 4px base, steps from `tokens.md` §3. Every margin, padding and gap is a step.
- **Proximity**: related items close (4–12px), groups apart (24–48px), sections far apart (64–128px). The ratio between inside-group and between-group spacing should be at least 2×.
- Use `gap` on flex/grid containers instead of margins on children.
- Padding inside a control scales with its size: `sm 8/12`, `md 10/16`, `lg 12/20` (vertical/horizontal).
- Section rhythm on marketing pages: consistent vertical padding (e.g. 96px desktop / 64px mobile), varied only on purpose.

## 2. Grid and containers

- Content container: `max-width` 1200–1280px for apps/marketing, 680–760px for reading, full-bleed for media sections.
- Side gutters: 16px mobile, 24px tablet, 32px+ desktop.
- 12-column grid on desktop, 4 on mobile; or simpler auto-fit grids: `grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr))`.
- Align everything to a few edges. Every new left edge is visual noise.
- App shells: sidebar 240–280px (collapsible to 64px icon rail), top bar 56–64px, content max-width for forms (~640px) even on wide screens.

## 3. Hierarchy

Ask of every screen: what is first, second, third? Then make it so with:
1. Position (top-start is read first; in RTL that is top-right).
2. Size and weight.
3. Contrast and color (one accent for the primary action).
4. Space around it (isolation creates emphasis).
Squint test: blur the screenshot; the primary element and action must still be obvious.

- One primary action per view. Secondary actions are outline/ghost; tertiary are links.
- Group by meaning; label groups with headings, not boxes. Cards only when an item is a distinct, actionable object; never cards inside cards.
- Remove borders where space already separates; remove space where a border already separates.

## 4. Responsive

- Mobile-first CSS. Design the 375px layout first; it forces priorities.
- Breakpoints change layout, not just size: stack → split, tabs → sidebar, sheet → dialog, table → cards/list.
- Container queries (`@container`) for components that live in different widths (cards in sidebar vs main).
- Use `dvh`/`svh` instead of `vh` for full-height mobile layouts (the URL bar changes `vh`).
- Respect safe areas on mobile web and apps: `padding: env(safe-area-inset-*)`.
- Touch: targets ≥ 44×44pt (WCAG 2.2 minimum 24×24 CSS px, but 44 is the comfortable floor), 8px between targets, primary actions in the thumb zone (bottom on phones).
- Tables on mobile: priority columns + expandable rows, or a card list; horizontal scroll only with a visible cue and sticky first column.
- Test at 320px (small phones, zoom 200%) — nothing overflows horizontally.

## 5. RTL layout

- Use logical properties: `margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `border-start-start-radius`, `text-align: start`. Tailwind: `ms-*`, `me-*`, `ps-*`, `pe-*`, `start-*`, `end-*`, `text-start`.
- Set `dir="rtl"` and `lang="ar"` on `<html>`; components follow automatically.
- Mirror: navigation order, back/forward arrows, progress direction, sliders, carousels, breadcrumbs, chevrons, drawer side.
- Don't mirror: media playback controls (play is ▶), clocks, numbers, logos, checkmarks, charts' time axis convention per audience (keep consistent), phone numbers.
- Icons with direction get `rtl:-scale-x-100` (or a mirrored variant).
- `i18n-rtl` skill + `rtl_lint.py` catch physical properties.

## 6. Simplify a layout (distill)

1. List every element on the screen and its job. Delete what has none.
2. Merge duplicates (two "save" buttons, two search fields).
3. Replace explanation text with a better label or default.
4. Move rare actions into a menu ("⋯"), keep frequent ones visible.
5. Collapse advanced options behind a disclosure.
6. Check the step count of the main flow; remove a step if a default or inline edit can replace it.

## 7. Density

- Comfortable (default): row height 48–56px, control height 40px.
- Compact (data tools): row height 32–40px, control height 32px, 14px text.
- Offer a density toggle in data-heavy tools; persist it.
