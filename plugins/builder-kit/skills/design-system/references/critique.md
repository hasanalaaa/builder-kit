# Critique and audit

## 1. Capture before judging

- Screens: every key screen of the flow under review, at 375 / 768 / 1280, light + dark, LTR + RTL.
- States: empty, loading, error, long content, no permission.
- Flow: record step counts for the main tasks.
- Code signals: `design_lint.py <src> --stats`, `contrast.py --tokens <file>`.
- Context: `SPEC.md`, `DESIGN.md`, target users, surface mode.

## 2. Scored rubric (0–4 each; 4 = excellent, 2 = acceptable, 0 = broken)

| # | Dimension | Questions |
|---|-----------|-----------|
| 1 | Clarity of purpose | Can a first-time user say what this screen is for in 5 seconds? |
| 2 | Hierarchy | Is the primary element/action obvious (squint test)? |
| 3 | Task efficiency | Steps to complete the main task; avoidable fields, clicks, confirmations? |
| 4 | Consistency | Same patterns, tokens, words for the same things? |
| 5 | Feedback & states | Does every action respond? Are loading/empty/error/success designed? |
| 6 | Error prevention & recovery | Defaults, constraints, undo, clear error messages? |
| 7 | Typography | Scale, measure, line height, pairing, Arabic quality |
| 8 | Color & contrast | Purposeful color, WCAG pass, dark mode quality |
| 9 | Layout & spacing | Grid, alignment, rhythm, proximity |
| 10 | Responsiveness | Mobile layout designed (not squeezed), touch targets, no overflow |
| 11 | Accessibility | Keyboard, focus, labels, semantics, reduced motion |
| 12 | Content & copy | Clear, specific, consistent, native Arabic |
| 13 | Distinctiveness | Does it look authored for this product, or generic AI? |
| 14 | Craft details | Browser surfaces themed, icon consistency, image quality, micro-interactions |

Score /56 → percentage. < 60% needs structural work; 60–80% polish; > 80% ship-ready with fixes.

Heuristic cross-check (Nielsen's 10): visibility of status, match with real world, user control & freedom, consistency, error prevention, recognition over recall, flexibility & efficiency, aesthetic & minimalist design, error recovery, help & documentation.

## 3. Severity

| Level | Meaning | Examples |
|-------|---------|----------|
| Critical | Blocks a task or excludes users | Can't submit on mobile, keyboard trap, contrast 2:1 on body, broken RTL layout |
| High | Causes errors or abandonment | Unclear primary action, no error messages, lost input on error |
| Medium | Slows or confuses | Inconsistent terms, extra steps, weak hierarchy |
| Low | Polish | Spacing off-scale, unthemed selection color |

## 4. Report format (`DESIGN_REVIEW.md`)

```markdown
# Design review: <scope> · <date>
Score: <n>/56 (<pct>%) · Surface mode: <mode> · Screens reviewed: <list>

## Summary (≤ 5 lines)

## Scores
| Dimension | Score | Note |

## Findings
| ID | Severity | Where (screen/component, file:line) | Problem | Fix (specific) | Effort S/M/L |

## What works (keep)

## Quick wins (≤ 1 hour each)

## Tool output
design_lint: <n> ERROR, <n> WARN · contrast: <n> failing pairs
```

Fixes are concrete ("Increase muted-foreground from neutral-400 to neutral-600 to reach 4.6:1"), never "improve contrast".

## 5. Audit (technical) checklist

- Semantics: landmarks, headings in order, buttons vs links, lists, tables with headers.
- Forms: labels, autocomplete, error association, input types.
- Images: alt, dimensions, formats, lazy loading.
- Performance: LCP element, font loading, CLS sources, JS weight (performance skill).
- Tokens: raw values count (`design_lint.py --stats`).
- i18n: `lang`/`dir`, logical properties, string externalization, number/date formatting.
- Dark mode and reduced motion implemented.
