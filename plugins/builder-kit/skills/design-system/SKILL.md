---
name: design-system
description: Professional UI/UX design for websites, web apps, dashboards, landing pages, mobile (iOS/Android) and desktop apps - choosing a distinct visual direction, building a token-based design system (color, type, spacing, radius, elevation, motion), designing screens and components with every state, Arabic/RTL-first typography, UX copy, critique with scored rubrics, and a final polish pass. Ships a searchable design database (products, styles, palettes, Arabic+Latin fonts, 100+ UX rules, landing and chart guides), a palette generator, a WCAG/APCA contrast checker, and design_lint.py for AI-slop and craft defects. Use for any UI work - design, redesign, build a screen or component, make it beautiful/professional/premium, critique, audit, polish, bolder, quieter, simplify, colors, fonts, typography, spacing, layout, dark mode, animation, empty states, onboarding, UX writing, design tokens, DESIGN.md. Also تصميم, واجهة, شكل الموقع, ألوان, خطوط, تجربة المستخدم, خلّيه احترافي, نظام تصميم.
---

# Design System

Design here means decisions that a user feels: what they see first, what they can do, how sure they are it worked. The goal is work that looks authored, not assembled: a clear point of view, consistent tokens, every state handled, and no trace of the generic AI look (purple gradients, identical icon cards, gradient text, emoji icons, eyebrow labels above every heading).

## 0. Setup (once per project, then on every UI task)

1. Read `SPEC.md` (product, users, platforms, languages) and `DESIGN.md` if it exists. `DESIGN.md` is the design source of truth: brief, direction, tokens, component rules. No `DESIGN.md` and the task is new UI → run **DIRECTION** first. A narrow fix on existing UI → infer the system from the code (EXTRACT §3.6 lite) and proceed.
2. Get a starting recommendation from the database:
   `python3 <skill>/scripts/design_search.py --recommend "<product, audience, mood, platform>"`
   It returns the product archetype, surface mode, candidate styles, palette seeds, Arabic+Latin font pairings, landing pattern and the UX rules that matter most. It is a starting point, not the answer: the brief wins.
3. Before any UI edit, read `references/craft-floor.md`. It is the quality floor and the ban list.

| File | Use it for |
|------|-----------|
| `references/direction.md` | Surface modes, the visual-world catalog, choosing and committing to a direction, `DESIGN.md` brief template, redesign vs refinement |
| `references/tokens.md` | Token architecture (primitive → semantic → component), naming, CSS variables, Tailwind v4 `@theme`, shadcn mapping, dark mode, density, radius, elevation, z-index, motion tokens |
| `references/color.md` | OKLCH palettes, 60-30-10, semantic colors, contrast (WCAG 2.2 + APCA), dark mode, color-blind safety, brand color fitting |
| `references/typography.md` | Type scales, fluid type, measure, line height, font pairing, Arabic typography, mixed Arabic/Latin, numerals, font loading |
| `references/layout.md` | Spacing scale, grids, containers, hierarchy, rhythm, responsive breakpoints, container queries, density, alignment |
| `references/components.md` | Anatomy, states and rules for ~30 components: buttons, inputs, forms, selects, dialogs, sheets, toasts, tables, cards, nav, tabs, menus, empty states, skeletons, uploads, search, command palette, charts |
| `references/patterns.md` | Screen patterns: landing, pricing, auth, onboarding, dashboard, settings, list/detail, tables, e-commerce, checkout, AI chat, mobile tab apps, content pages, data viz choice |
| `references/motion.md` | Durations, easing, choreography, what to animate, reduced motion, performance |
| `references/ux-copy.md` | Microcopy: buttons, errors, empty states, confirmations, tone, Arabic copy |
| `references/craft-floor.md` | The quality floor, verification list and AI-slop bans. Read before every UI edit |
| `references/critique.md` | CRITIQUE and AUDIT: scored rubric, heuristics, severity, report format |
| `references/native.md` | iOS (HIG) and Android (Material 3) specifics: navigation, touch targets, safe areas, dynamic type, haptics, platform controls |
| `data/*.csv` | The design database read by `design_search.py`: products, styles, palettes, fonts, ux-rules, landing, charts |
| `scripts/design_search.py` | `--recommend "<brief>"` for a starting design brief; `<query> [--domain styles\|fonts\|ux-rules…]` to search |
| `scripts/palette.py` | Brand hex or hue → full OKLCH scales + semantic light/dark tokens with contrast enforced; outputs CSS, Tailwind v4 `@theme` or JSON |
| `scripts/contrast.py` | WCAG 2.2 ratio and APCA Lc for color pairs, or every `X` / `X-foreground` pair in a CSS tokens file |
| `scripts/design_lint.py` | Static scan of CSS/TSX/JSX/HTML/Vue/Svelte for craft and a11y defects and AI-slop patterns. Run after every UI change; 0 ERROR to finish |

## 1. Principles

1. **The brief wins.** A pinned brand, palette, font or era from the user beats every default here and every database suggestion.
2. **Refinement preserves; redesign replaces.** Refining keeps identity, copy, behavior and everything outside the task. Redesigning keeps product truth and content but treats the old look as evidence, picks a new world (`direction.md`), and replaces `DESIGN.md`. Never half-polish a look you were asked to replace.
3. **Decide every axis on purpose.** Color, type, density, shape, depth, motion, imagery, tone of voice. If an axis was not decided, it defaulted, and defaults are where the generic look comes from.
4. **Tokens only.** Components use semantic tokens (`--color-fg-muted`, `--space-4`, `--radius-md`), never raw hex, px or ad-hoc values. One change in `DESIGN.md`/tokens restyles the product.
5. **Every state is designed.** Default, hover, focus-visible, active, disabled, loading, empty, error, success, no-permission, offline, long content, RTL, dark.
6. **Arabic and RTL are first-class.** Logical properties, mirrored layout, Arabic-capable fonts with proper sizes and line height, Arabic copy written natively (not translated word by word). See `typography.md` §5 and the `i18n-rtl` skill.
7. **Accessible by construction.** WCAG 2.2 AA: contrast, focus, keyboard, target size ≥ 24px (44pt touch on mobile), labels, reduced motion. Not a later pass (see `accessibility` skill).
8. **Fewer steps, clearer actions.** One primary action per view. Fewer fields, smart defaults, inline editing, undo over confirm (`project-architecture` law 11).
9. **Verify by looking.** Render the result at 375, 768 and 1280 px (and the shipped mobile sizes), light and dark, LTR and RTL. Batch checks into one look, fix, look again. A design you have not seen rendered is not done.
10. **Ambition fits the surface.** Marketing and brand surfaces get bold, committed, memorable work. Tools, dashboards and forms get precision and calm, where familiar patterns earn their place.

## 2. Surface modes (pick one per screen, from `direction.md` §1)

| Mode | Examples | Ambition shows as |
|------|----------|-------------------|
| **Tool** | dashboards, admin, editors, settings, forms | density control, alignment, speed, keyboard flow, quiet color with one accent |
| **Content** | blogs, docs, news, long reads, help centers | type, measure, rhythm, reading comfort, images |
| **Persuade** | landing pages, pricing, product pages, campaigns | a strong visual idea, hierarchy that sells, one authored motion moment |
| **Experience** | portfolios, brand sites, games, launches | expressive type, art direction, rich motion, surprise |

## 3. Modes of work

### 3.1 DIRECTION: new product or full redesign
1. Brief (`direction.md` §5): product, audience, use scene (who, where, what light, what device), brand attributes as 3 adjectives + 3 anti-adjectives, references the user likes and dislikes.
2. Run `design_search.py --recommend`. Read the matched styles, palettes, font pairings.
3. Propose **2–3 distinct directions** (`direction.md` §3), each: name, one-line idea, palette seed, font pairing, shape/depth/motion choices, a rendered sample (hero + one product screen) when possible. Not three variations of one idea.
4. User picks (or you pick the strongest and say why, if told to proceed).
5. Generate tokens: `python3 <skill>/scripts/palette.py --brand <hex> --name <name> --format css` (or `tailwind`) and the type/space/radius/shadow/motion scales from `tokens.md`.
6. Write `DESIGN.md` (template `direction.md` §5) and the tokens file. Build the core components (`components.md`), then screens.
7. Verify (§4).

### 3.2 BUILD: a screen or component
1. Read `DESIGN.md` + tokens. Find the nearest existing screen/component and follow it (`project-architecture` law 6: search before you create).
2. Pick the pattern from `patterns.md` and the components from `components.md`. Write the states table first (§1 rule 5).
3. Build with tokens only. Real content (real names, real lengths, Arabic and English), never lorem ipsum.
4. Read `craft-floor.md`, then verify (§4).

### 3.3 CRITIQUE / AUDIT: review existing UI
Follow `critique.md`: capture screens (all breakpoints, states, themes, directions), score the rubric, list findings by severity with exact fixes, run `design_lint.py` and `contrast.py --tokens`. Produce `DESIGN_REVIEW.md`. Change nothing until the user approves, unless asked to fix.

### 3.4 POLISH: before shipping
`craft-floor.md` §1 verification list on every screen, plus: browser surfaces themed (selection, focus ring, scrollbar, caret), copy pass (`ux-copy.md`), states complete, motion pass (`motion.md`), `design_lint.py` 0 ERROR, contrast 0 failures, RTL and dark checked.

### 3.5 REFINE: targeted improvements (pick by request)
| Request | Do |
|---------|-----|
| bolder / more premium / stand out | Commit harder on one axis: scale contrast in type, one signature color moment, art-directed imagery, one authored motion moment. `direction.md` §4 |
| quieter / calmer / less busy | Remove decoration, reduce color to neutrals + one accent, unify radii and shadows, slow motion down. `direction.md` §4 |
| simplify / distill / fewer clicks | Remove elements that don't serve the main job, merge steps, defaults, inline edit. `layout.md` §6 + `project-architecture/references/simplify.md` §3 |
| colorize | Introduce color by meaning (state, category, brand moment), not decoration. `color.md` §6 |
| typeset / fonts | Fix the scale, pairing, measure, weights; Arabic sizing. `typography.md` |
| layout / spacing | Rebuild on the spacing scale and grid; group by proximity. `layout.md` |
| animate | Add motion with a purpose. `motion.md` |
| clarify / copy | Rewrite labels, errors, empty states. `ux-copy.md` |
| responsive / adapt | Mobile-first rebuild of the layout; container queries; touch targets. `layout.md` §4, `native.md` |
| harden | Every state, long and short content, RTL, slow network, errors, permissions. `components.md` §0 |
| onboarding / empty states | First-run path to first value; empty states that teach and offer the action. `patterns.md` §4 |

### 3.6 EXTRACT: turn an existing UI into a system
1. Inventory: every color, font size, spacing, radius, shadow, z-index and breakpoint used (grep the code; `design_lint.py --stats` lists raw values).
2. Cluster near-duplicates (e.g. 7 grays → a 10-step neutral scale; 13 font sizes → a 7-step scale).
3. Write tokens (`tokens.md`), map old values to tokens, replace in small, verified steps.
4. Write `DESIGN.md` describing what exists. Document components and their variants.

## 4. Verify (every UI change)

- [ ] `python3 <skill>/scripts/design_lint.py <src>` → 0 ERROR; each WARN fixed or justified.
- [ ] `python3 <skill>/scripts/contrast.py --tokens <tokens.css>` → no failing pair.
- [ ] Rendered and looked at: 375 / 768 / 1280 px, light + dark, LTR + RTL, with real content (long names, long Arabic words, empty lists, 1 item, 1,000 items).
- [ ] Every state from §1 rule 5 exists and was seen.
- [ ] Keyboard only: tab order logical, focus visible everywhere, no traps; screen-reader names on icon buttons.
- [ ] `craft-floor.md` verification list passes.
- [ ] `DESIGN.md` updated if tokens, components or direction changed.

## 5. Hand-offs

- Accessibility depth → `accessibility`. RTL/i18n mechanics → `i18n-rtl`. Front-end code quality (state, forms) → `frontend-quality`. Speed (images, fonts, CLS) → `performance`. Native app conventions → `native.md` here plus `mobile-release`.
- Installed companions, when present, can add depth: `impeccable` (live browser iteration and its detector), `ui-ux-pro-max` (larger catalogs). This skill's `DESIGN.md` stays the source of truth.
