# Components: anatomy, states, rules

## 0. The states table (write it before building)

| State | What the user sees | Notes |
|-------|--------------------|-------|
| default | | |
| hover | subtle surface/border change | pointer devices only (`@media (hover: hover)`) |
| focus-visible | 2px ring, offset 2px, ≥ 3:1 contrast | never remove without replacement |
| active / pressed | slight darken or scale(0.98) | instant feedback |
| disabled | lowered contrast + `cursor: not-allowed`; explain why nearby when not obvious | prefer enabled + validation message over disabled submit buttons |
| loading | spinner/skeleton in place, same size, label kept or "Saving…" | prevent double submit |
| empty | explanation + primary action | see patterns.md §4 |
| error | message near the cause, how to fix | icon + text, not color only |
| success | confirmation that matches the action's weight | toast for small, page for big |
| no permission | say why and who can grant it | |
| offline / slow | cached data + banner, retry | mobile especially |
| long content | truncation with tooltip/expand, wrapping, Arabic long words | test with real lengths |

## 1. Buttons

- Variants: primary (one per view), secondary, outline, ghost, destructive, link. Sizes sm/md/lg = 32/40/48px.
- Label = verb + object ("Create invoice", "إنشاء فاتورة"). Not "OK", "Submit", "Click here".
- Icon + label beats icon alone. Icon-only buttons need `aria-label` and a tooltip.
- Loading: keep width, show spinner, set `aria-busy`, disable repeat clicks.
- Destructive: red only for the final confirm; the entry point can be neutral. Prefer undo over confirmation dialogs for reversible actions.
- Order: primary at the end of reading direction in dialogs (right in LTR, left in RTL) on web; follow platform on native.

## 2. Text inputs and forms

- Visible label above the field (never placeholder-as-label). Optional fields marked "(optional)"; don't asterisk everything.
- Helper text below; error replaces/joins helper, in danger color with icon, linked via `aria-describedby`.
- Validate on blur and on submit; don't shout errors while typing the first time. Re-validate live after an error appears.
- Right `type`, `inputmode`, `autocomplete` (`email`, `tel`, `one-time-code`, `new-password`, `street-address`) so mobile keyboards and password managers work.
- Height 40–48px; font-size ≥ 16px on mobile.
- One column forms. Group with headings. Put related short fields side by side only when they belong together (city + postal code).
- Submit button states: idle → loading → success/error. On error, focus the first invalid field and summarise at top for long forms.
- Don't disable paste in password/OTP fields. Show/hide password toggle.
- Save drafts for long forms; warn on leaving with unsaved changes.

## 3. Selection controls

- ≤ 5 options: radio group (single) or checkboxes (multi) — visible, one click.
- 6–15: select/dropdown. > 15: combobox with search.
- Binary immediate setting: switch (applies instantly). Binary in a form submitted later: checkbox.
- Dates: native `<input type="date">` on mobile; a calendar picker on desktop for ranges; always allow typing. Show format, respect locale and calendar (Gregorian/Hijri where relevant).
- Segmented control for 2–4 mutually exclusive views.

## 4. Dialogs, sheets, popovers

- Dialog (modal) only when the task needs focus and must block: destructive confirm, short focused form. Not for content that could be a page.
- Focus trapped inside, initial focus on the first field (or the least destructive button), Escape closes, focus returns to the trigger. Use `<dialog>` or a tested primitive (Radix, React Aria).
- Mobile: bottom sheet instead of centered modal.
- Popover for small contextual content; tooltip only for short labels (never essential info, never interactive content).
- Never stack modals.

## 5. Feedback

- Toasts: short, auto-dismiss 4–6s (longer if there's an action), pause on hover, Undo action when reversible, `role="status"` (polite). Errors that need action are inline, not toasts.
- Banners: page-level state (offline, trial ending, maintenance).
- Inline validation and inline success ("Saved ✓" next to the field).
- Progress: determinate bar when you know the length; skeletons for content loading (< 1s no indicator, 1–3s skeleton/spinner, > 3s progress with explanation).
- Skeletons match the final layout's shape; no shimmer on reduced motion.

## 6. Navigation

- Web app: sidebar for 5+ sections, top tabs for 2–5. Current location always visible (active state + page title + breadcrumb for deep trees).
- Mobile: bottom tab bar with 3–5 destinations, labels under icons. Hamburger menus hide navigation; use only for secondary items.
- Marketing header: logo, ≤ 6 links, one CTA. Sticky header on long pages, shrunk on scroll.
- Links look like links. Navigation items are links (`<a>`), actions are buttons.
- Command palette (⌘K) for power tools with many destinations/actions.

## 7. Tables and lists

- Align numbers to the end (right in LTR), text to the start. Tabular numerals. Units in the header, not each cell.
- Sticky header; sortable columns show sort direction; filters visible as chips.
- Row actions: one primary visible, rest in a "⋯" menu. Bulk actions appear when rows are selected.
- Pagination or "load more" for > 50 rows; virtualize for > 500.
- Empty, loading (skeleton rows), error (retry) and "no results for filter" (clear filters action) states are all different.
- Mobile: collapse to cards showing 2–3 key fields.

## 8. Cards

- Use for distinct objects (a project, a product), not as a default container for every section.
- One clickable area per card (whole card link) or explicit buttons, not both nested.
- Consistent padding (16–24px), radius from tokens, either border or shadow, not both heavy.
- No nested cards.

## 9. Empty states

Three parts: what this is, why it's empty, the action to fill it. Optional small illustration. Variants: first use (teach + CTA), no results (adjust/clear filters), cleared (celebrate inbox zero), error (what failed + retry), no permission.

## 10. File upload

Drop zone + button, accepted types and max size stated before upload, per-file progress, cancel, error per file with reason, preview for images, keyboard accessible. Server-side validation still required (launch-security 18).

## 11. Search

Visible field on content-heavy products; ⌘K/"/" shortcut on tools; recent searches; results grouped; highlight matches; "no results" with suggestions; debounce 200–300ms; works in Arabic (normalize alef/hamza/taa marbuta/diacritics on the server).

## 12. Avatars, badges, tags

Avatars: image with initials fallback (Arabic initials work: first letter of first + last name), consistent sizes. Badges for counts (cap at 99+). Status pills: dot/icon + text.

## 13. Charts

Pick from `data/charts.csv` (`design_search.py "<data shape>" --domain charts`). Rules: title says the insight; direct labels over legends; start bar axes at zero; ≤ 7 series; accessible table or summary alternative; tooltips keyboard reachable; colors from `color.md` §7.

## 14. Icons

One library (Lucide, Phosphor, Heroicons, Tabler, SF Symbols on iOS, Material Symbols on Android), one stroke width, 2–3 sizes (16/20/24). Never emoji or Unicode glyphs as UI icons. Decorative icons `aria-hidden="true"`; meaningful icons get a label.

## 15. Images and media

Correct aspect ratios (`aspect-ratio`), `object-fit: cover` with a focal point, explicit width/height to prevent layout shift, alt text describing purpose (empty alt for decoration), lazy-load below the fold, modern formats (AVIF/WebP). Video: poster, captions, no autoplay with sound, controls available.
