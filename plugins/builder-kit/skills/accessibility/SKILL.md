---
name: accessibility
description: Make websites and apps usable by everyone and compliant with WCAG 2.2 AA (and the European Accessibility Act, ADA, Section 508) - semantic HTML, keyboard access, focus management, screen-reader names and announcements, color contrast, target size, forms and errors, motion, media captions, ARIA patterns for dialogs/menus/tabs/comboboxes, RTL and Arabic screen readers, and native iOS/Android accessibility (VoiceOver, TalkBack, Dynamic Type). Use when building any UI, reviewing for a11y, fixing keyboard or screen-reader issues, preparing for an accessibility audit or legal requirement, or when the user says accessibility, a11y, WCAG, screen reader, keyboard navigation, إمكانية الوصول, ذوي الإعاقة, قارئ الشاشة. Ships a11y_lint.py (missing alt, unlabeled inputs and icon buttons, clickable divs, positive tabindex, missing lang, iframe titles, aria-hidden on focusables, heading skips, autoplay).
---

# Accessibility

About one in six people lives with a disability, and everyone is temporarily impaired sometimes (bright sun, broken arm, noisy room, slow connection). Accessible UI is also better UI: clear labels, visible focus, good contrast and predictable behavior help every user, search engines and AI agents that operate your app. Build it in; retrofitting is several times more expensive.

| File | Use it for |
|------|-----------|
| `references/wcag-checklist.md` | WCAG 2.2 AA checklist grouped by task (structure, keyboard, focus, names, forms, color, motion, media, mobile), the 2.2 additions, ARIA patterns, testing procedure with tools and screen readers, native iOS/Android, legal notes |
| `scripts/a11y_lint.py` | Static checks in JSX/TSX/HTML/Vue/Svelte: img alt, input labels, icon-only buttons, click handlers on non-interactive elements, `<a>` without href, positive tabindex, autofocus, iframe title, `<html lang>`, aria-hidden on focusable, heading level skips, autoplay media, React Native touchables without accessibility labels |

## 1. Rules

1. **Native HTML first.** `<button>`, `<a href>`, `<label>`, `<input>`, `<select>`, `<dialog>`, `<details>`, headings, lists, tables, landmarks (`header`, `nav`, `main`, `footer`). ARIA only to fill gaps; "no ARIA is better than bad ARIA".
2. **Everything works with a keyboard**: reachable in logical order, operable (Enter/Space/Arrows/Escape as the pattern expects), focus always visible, no traps, skip link to main content.
3. **Every control has an accessible name** that matches its visible label; icon-only buttons get `aria-label`; images have purposeful `alt` (empty for decoration).
4. **Forms**: visible labels, instructions before input, errors identified in text, associated with the field (`aria-describedby`), and focus moved to the first error; don't ask users to re-enter info (WCAG 3.3.7); no cognitive tests for login (3.3.8: allow paste, password managers, passkeys).
5. **Contrast and color**: text 4.5:1 (large 3:1), UI and focus indicators 3:1, never color alone (`design-system` contrast tools).
6. **Target size ≥ 24×24 CSS px** (WCAG 2.2) and 44pt/48dp on touch; focused element not hidden behind sticky headers (2.4.11).
7. **Motion and time**: respect reduced motion, no flashing, pause for moving content, extendable timeouts, alternatives to dragging (2.5.7).
8. **Dynamic changes are announced**: live regions for status and errors, focus moved to new content on route change and dialog open, returned on close.
9. **Language and direction declared** (`lang`, `dir`), and changes marked inline (`<span lang="en">`). Arabic screen readers need correct `lang="ar"` to pronounce.
10. **Test with real tools**: automated (axe) catches ~30–40%; keyboard pass and a screen-reader pass catch the rest.

## 2. Workflow

**Building**: follow rules while writing; use accessible primitives (Radix, React Aria, Headless UI, Ark, shadcn/ui built on Radix); run `python3 <skill>/scripts/a11y_lint.py .`; add `@axe-core/playwright` checks to E2E; do a keyboard pass on each new screen.

**Auditing**: follow `wcag-checklist.md` §10 procedure; record findings with WCAG criterion, severity, location, fix; produce `ACCESSIBILITY_REPORT.md` (same format as `design-system/references/critique.md` §4) and, if needed, an accessibility statement page.

## 3. Done when

- [ ] `a11y_lint.py` 0 ERROR; axe has 0 serious/critical violations on key pages (light, dark, RTL).
- [ ] Keyboard-only pass completes every main flow; focus visible and logical; no traps.
- [ ] Screen-reader pass (VoiceOver or NVDA; TalkBack/VoiceOver on mobile) on the main flows: names, roles, states, announcements make sense, in Arabic and English.
- [ ] Contrast, target size and reduced motion verified.
- [ ] Forms: labels, errors, focus on error, no re-entry, accessible authentication.
