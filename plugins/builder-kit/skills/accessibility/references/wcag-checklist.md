# WCAG 2.2 AA checklist and testing

Criteria numbers in parentheses. Grouped by what you build, not by spec order.

## 1. Structure and semantics
- [ ] One `h1` per page; headings nested without skipping levels; headings describe sections (1.3.1, 2.4.6).
- [ ] Landmarks: `header`, `nav` (labelled if several), `main` (one), `aside`, `footer` (1.3.1).
- [ ] Lists are `ul/ol/li`; tables of data use `table`, `th` with `scope`, `caption` (1.3.1).
- [ ] Reading order in the DOM matches visual order (1.3.2); CSS reordering doesn't break meaning.
- [ ] Page `<title>` unique and descriptive, updated on client route changes (2.4.2).
- [ ] `lang` on `<html>`; `lang` on inline passages in another language (3.1.1, 3.1.2).
- [ ] Content reflows at 320 CSS px without horizontal scroll (1.4.10); text resizes to 200% (1.4.4); text spacing overrides don't break layout (1.4.12).
- [ ] Orientation not locked (1.3.4).

## 2. Keyboard
- [ ] Every interactive element reachable with Tab and operable with keyboard (2.1.1).
- [ ] No keyboard trap; Escape closes overlays (2.1.2).
- [ ] Skip link to `main` as first focusable element (2.4.1).
- [ ] Focus order logical (2.4.3); no positive `tabindex`.
- [ ] Single-key shortcuts can be turned off or remapped (2.1.4).
- [ ] Composite widgets (menus, tabs, listboxes, grids) use arrow keys with roving tabindex per ARIA APG.

## 3. Focus
- [ ] Focus indicator visible on every focusable element (2.4.7), ≥ 3:1 against adjacent colors, not removed with `outline: none` without replacement.
- [ ] Focused element not entirely hidden by sticky headers/footers/cookie banners (2.4.11): use `scroll-padding-top`.
- [ ] Focus moves into dialogs on open, is trapped inside, returns to the trigger on close.
- [ ] On SPA route change: move focus to the new page's `h1` (or main) and announce the page.
- [ ] No context change on focus or input alone (3.2.1, 3.2.2).

## 4. Names, roles, values
- [ ] Every control has an accessible name (4.1.2); visible label text is contained in the accessible name (2.5.3).
- [ ] Icon-only buttons: `aria-label`; decorative icons `aria-hidden="true"`.
- [ ] Images: meaningful `alt`; decorative `alt=""`; complex images (charts) have text alternatives (1.1.1).
- [ ] Links describe their destination (2.4.4): no bare "click here"/"read more" without context.
- [ ] Custom widgets expose state: `aria-expanded`, `aria-selected`, `aria-checked`, `aria-pressed`, `aria-current`.
- [ ] Status messages announced without focus via `role="status"`/`aria-live="polite"`; errors with `role="alert"` (4.1.3).

## 5. Forms
- [ ] Labels for every input (`<label for>` or wrapping); placeholders aren't labels (3.3.2).
- [ ] Required fields indicated in text; input purpose via `autocomplete` (1.3.5).
- [ ] Errors: identified in text, describe the fix, associated with the field, focus moves to first error, summary for long forms (3.3.1, 3.3.3).
- [ ] Legal/financial/data submissions are reversible, checked, or confirmed (3.3.4).
- [ ] Don't ask for the same info twice in a process; auto-fill or offer to reuse (3.3.7, new in 2.2).
- [ ] Authentication without cognitive tests: allow paste, password managers, passkeys, magic links; CAPTCHAs have accessible alternatives (3.3.8, new in 2.2).
- [ ] Help (contact, chat, FAQ) in the same place across pages (3.2.6, new in 2.2).

## 6. Color and contrast
- [ ] Text 4.5:1, large text 3:1 (1.4.3); UI components and graphical objects 3:1 (1.4.11).
- [ ] Color not the only means of conveying information (1.4.1).
- [ ] Check in light, dark, high-contrast modes and on hover/focus/disabled states.

## 7. Pointer and touch
- [ ] Target size ≥ 24×24 CSS px or enough spacing (2.5.8, new in 2.2); 44pt/48dp on mobile.
- [ ] Anything done by dragging has a single-pointer alternative (2.5.7, new in 2.2): sortable lists with up/down buttons, sliders with input.
- [ ] Multi-point/path gestures have single-tap alternatives (2.5.1); actions fire on up-event, cancellable (2.5.2).
- [ ] Motion-actuated features (shake) have UI alternatives (2.5.4).

## 8. Motion, time, media
- [ ] `prefers-reduced-motion` respected; parallax and auto-animations reduced.
- [ ] Moving/auto-updating content > 5s can be paused (2.2.2); nothing flashes > 3/s (2.3.1).
- [ ] Time limits adjustable/extendable (2.2.1).
- [ ] Video: captions (1.2.2), audio description or transcript (1.2.3/1.2.5); live captions for live video (1.2.4).
- [ ] Audio doesn't autoplay for > 3s without control (1.4.2).

## 9. Arabic and RTL specifics
- [ ] `lang="ar"` + `dir="rtl"`; mixed English terms wrapped with `lang="en"` for correct pronunciation.
- [ ] Screen readers (VoiceOver Arabic, NVDA with Arabic voice, TalkBack) read in the right order; icons mirrored only visually.
- [ ] Don't use Arabic letters as icon fonts or decoration with meaning without text alternatives.
- [ ] Numbers: be consistent (Western vs Arabic-Indic digits) so speech output is predictable.

## 10. Testing procedure

1. **Automated**: `a11y_lint.py`; axe (`@axe-core/playwright` in E2E, axe DevTools extension), Lighthouse accessibility, eslint-plugin-jsx-a11y in the editor.
2. **Keyboard**: unplug the mouse; complete each main flow; note focus visibility, order, traps, Escape.
3. **Screen reader** (at least one desktop + one mobile):
   - macOS VoiceOver (Cmd+F5) with Safari; Windows NVDA (free) with Firefox/Chrome; iOS VoiceOver; Android TalkBack.
   - Navigate by headings, landmarks, form controls; listen to names/roles/states; trigger errors and toasts.
4. **Zoom and reflow**: 200% and 400% zoom, 320px width; OS text size large.
5. **Contrast**: `design-system/scripts/contrast.py --tokens`; check images of text.
6. **Reduced motion and high contrast**: toggle OS settings (forced-colors mode on Windows).
7. **Report**: criterion, severity (blocker/high/medium/low), location, user impact, fix, retest status.

## 11. ARIA patterns (follow the WAI-ARIA Authoring Practices)

| Widget | Key requirements |
|--------|------------------|
| Dialog (modal) | `role="dialog"` + `aria-modal="true"` + `aria-labelledby`; focus trap; Escape; return focus. Native `<dialog>` with `showModal()` handles much of it |
| Menu button | `aria-haspopup="menu"`, `aria-expanded`; arrow keys inside; Escape returns focus |
| Tabs | `role="tablist"/"tab"/"tabpanel"`, `aria-selected`, `aria-controls`; arrows move between tabs |
| Combobox / autocomplete | `role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant`; announce result counts |
| Accordion | buttons with `aria-expanded` controlling regions; or native `<details>` |
| Toast | `role="status"` (polite) or `role="alert"` (urgent); not focus-stealing; long enough to read |
| Tooltip | `role="tooltip"`, shown on hover and focus, dismissible with Escape, never the only place for essential info |
| Disclosure nav | button with `aria-expanded`; links inside |
| Data grid | prefer a simple table; full grid pattern only for spreadsheet-like interaction |

Use tested libraries (Radix, React Aria, Headless UI, Ark UI) instead of hand-rolling these.

## 12. Native apps

**iOS**: every control `accessibilityLabel` (SwiftUI `.accessibilityLabel`), `accessibilityHint` sparingly, traits (`.isButton`, `.isHeader`), group related elements (`.accessibilityElement(children: .combine)`), Dynamic Type for all text, 44pt targets, `UIAccessibility.post(notification: .announcement…)` for status, support Reduce Motion and Increase Contrast, test with VoiceOver and Accessibility Inspector.

**Android**: `contentDescription` on images/icon buttons (Compose `Modifier.semantics { contentDescription = … }`), `heading()` semantics, 48dp targets, `sp` text sizes, live regions for status, test with TalkBack and Accessibility Scanner.

**React Native**: `accessible`, `accessibilityRole`, `accessibilityLabel`, `accessibilityState`, `accessibilityHint`; `AccessibilityInfo.announceForAccessibility`; `allowFontScaling` stays on.

## 13. Legal landscape (informational, not legal advice)

- EU: European Accessibility Act applies to many consumer digital products/services (e-commerce, banking, e-books, transport) since 28 June 2025; harmonized standard EN 301 549 (maps to WCAG 2.1 AA, moving toward 2.2).
- US: ADA Title III lawsuits target websites and apps; Section 508 for federal; DOJ rule for state/local government sites (WCAG 2.1 AA).
- Many governments (including Gulf states) require WCAG AA for public-sector digital services.
- Publish an accessibility statement with known limitations and a contact for barriers.
