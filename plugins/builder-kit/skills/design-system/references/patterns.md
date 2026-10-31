# Screen patterns

Patterns are starting structures, not templates to stamp. Keep the job, adapt the form to the direction. `data/landing.csv` holds searchable landing structures.

## 1. Landing page (Persuade)

Order follows the visitor's questions: What is it? → Is it for me? → Does it work? → What does it cost? → What do I do now?

1. **Hero**: headline that states the outcome (not the feature), one-line subhead with who/how, primary CTA + secondary (demo/video), a real product visual or a strong art-directed image. Above the fold on mobile: headline + CTA visible.
2. **Proof strip**: customer logos, rating, a number that matters.
3. **Problem → solution** or **how it works** in 3 steps (only if the steps are real).
4. **Feature sections**: 2–4 alternating sections each with a real screenshot/demo and one benefit headline. Avoid the grid of identical icon cards.
5. **Testimonials** with name, role, photo, specific result.
6. **Pricing** summary or link.
7. **FAQ** answering real objections (price, security, cancel, data).
8. **Final CTA** repeating the primary action.
9. **Footer**: legal links, contact, language switch.

Conversion rules: one primary CTA label used everywhere; CTA contrast highest on the page; forms ask the minimum (email only to start); page loads fast (performance skill); no carousel for key messages.

## 2. Pricing

- 2–4 plans, recommended plan highlighted (not just colored: label "Most popular" + elevation).
- Monthly/annual toggle with savings shown; prices in local currency with tax clarity.
- Feature comparison table below, grouped; ✓ with text, not only icons.
- "What happens after the trial", cancel anytime, refunds — in plain words.
- Enterprise/contact plan when sales-led.

## 3. Authentication

- Sign up: email + password (or passkey / magic link / social) on one screen; social buttons first on consumer apps; Sign in with Apple required on iOS when other social logins exist.
- Password rules shown up front, strength meter, show/hide toggle, paste allowed.
- Sign in: "Forgot password?" next to the field; errors don't reveal which field was wrong.
- Verification code: `autocomplete="one-time-code"`, numeric inputmode, auto-advance, paste whole code, resend timer.
- After auth → straight into the product's first value, not a blank dashboard.

## 4. Onboarding and first run

- Goal: the user reaches first value (the "aha") in as few steps as possible.
- Ask only what personalizes the first screen (role, goal); skip everything else.
- Prefer doing over touring: a checklist of 3–5 real tasks, progress shown, dismissible.
- Seed data or templates so screens aren't empty; mark sample data clearly.
- Empty states (components.md §9) are part of onboarding.
- Ask for permissions (notifications, location) at the moment they're needed, with a pre-prompt explaining why.

## 5. Dashboard (Tool)

- Start from the user's top 3 questions; each gets one widget. No "metrics because we have them".
- Top row: 3–5 KPIs with comparison (vs last period) and sparkline only if trend matters.
- Primary chart below; tables of actionable items (what needs attention) above vanity charts.
- Date range and filters global and sticky; state in the URL.
- Every number clickable to its detail. Loading per widget, not one big spinner.
- Empty dashboard → onboarding checklist, not zeros.

## 6. List → detail (CRUD)

- List: search, filters, sort, bulk select, primary "New" button top-end.
- Detail: title + status + primary action in the header; tabs for sections; activity/history log; edit inline where fields are simple.
- Create: page for complex objects, dialog/sheet for simple ones (≤ 5 fields). After create, go to the new item or show it highlighted in the list.
- Delete: undo toast for soft delete; typed confirmation only for irreversible, high-impact deletion.

## 7. Settings

- Grouped navigation (Profile, Account, Notifications, Billing, Team, Security, Integrations, Danger zone last).
- Auto-save switches with inline confirmation; explicit Save for text forms, sticky save bar when dirty.
- Danger zone visually separated, destructive actions explained.

## 8. E-commerce

- Product page: gallery (zoom, swipe), price + availability near title, variant selectors as visible options, add-to-cart sticky on mobile, delivery estimate, returns info, reviews with filters.
- Cart: editable quantities, clear totals with tax/shipping, promo field collapsed, checkout CTA prominent.
- Checkout: guest checkout, minimal steps (contact → delivery → payment), address autocomplete, Apple Pay/Google Pay/local wallets on top, order summary always visible, trust markers near payment.
- Order confirmation: number, what happens next, delivery tracking.

## 9. AI chat / assistant UI

- Input pinned at bottom, grows with content, Enter to send (Shift+Enter newline; respect IME composition for Arabic input), stop button while generating.
- Stream tokens; show tool/step progress ("Searching documents…") rather than a silent spinner.
- Messages: user aligned to end, assistant to start (mirrored in RTL); markdown rendered safely; code blocks with copy; citations as links.
- Actions per message: copy, retry, feedback; edit last user message.
- Empty state: 3–4 starter prompts tied to real use cases.
- Errors: inline with retry; rate-limit message with time.
- Conversation list with search and rename; clear data controls.

## 10. Mobile app shells

- Tab bar (3–5) + stack navigation per tab. Large titles on iOS root screens.
- Pull to refresh on lists; swipe actions with visible alternatives; FAB on Android only when one action dominates.
- Bottom sheets for options; full-screen modals for creation flows.
- Offline: cached content + banner; queued actions with sync status.
- See `native.md` for platform specifics.

## 11. Content pages (blog, docs, help)

- Reading column 65–75ch, TOC for long pages (sticky on desktop), headings with anchor links.
- Code blocks with copy, callouts (note/warning) with icon + label.
- Search prominent in docs; "Was this helpful?" + edit link.
- Related articles at the end, not in the middle.

## 12. Error and system pages

- 404: say what happened, search + links to main sections, keep header/footer.
- 500/maintenance: apology, status page link, retry; no stack traces.
- Offline (PWA/mobile): what still works.

## 13. Choosing a chart (summary; full list in `data/charts.csv`)

| Question | Chart |
|----------|-------|
| Change over time | Line (many points), column (few periods) |
| Compare categories | Horizontal bar (sorted), dot plot |
| Part of whole (≤ 5 parts) | Stacked bar or donut with labels; otherwise bar |
| Distribution | Histogram, box plot |
| Relationship | Scatter (bubble for 3rd variable) |
| Geography | Choropleth (rates, not counts), symbol map |
| Single KPI | Big number + delta + small trend |
| Progress to goal | Progress bar with target marker |
