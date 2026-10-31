# Motion

Motion explains change: where something came from, where it went, what caused it. Motion that explains nothing is decoration and costs attention, battery and accessibility.

## 1. Purposes (each animation must have one)

1. **Feedback**: a press, a toggle, a saved state.
2. **Orientation**: a panel slides from the side it lives on; a detail expands from its card.
3. **Continuity**: shared-element transitions between list and detail.
4. **Attention**: one thing that needs noticing (a new notification), once.
5. **Brand moment**: one authored sequence on a Persuade/Experience surface (hero reveal, scroll story).

## 2. Timing

| Change | Duration |
|--------|----------|
| Hover, press, toggle, color | 100–150ms |
| Small element enter/exit (tooltip, menu, toast) | 150–220ms |
| Panels, dialogs, sheets | 220–320ms |
| Page/route transitions, large layout moves | 300–480ms |
| Brand/hero sequences | up to ~1000ms total, staggered 40–80ms per item |

Exits are faster than entrances (~70%). Bigger distance → slightly longer. Nothing interactive waits for an animation to finish.

## 3. Easing

- Entrances and most UI: ease-out (fast start, gentle stop): `cubic-bezier(0.16, 1, 0.3, 1)`.
- Moving between two on-screen positions: ease-in-out.
- Exits: ease-in.
- Never `linear` for movement (fine for spinners and progress).
- Springs (Framer Motion/Motion, SwiftUI, Reanimated) for draggable and gesture-driven UI: they respond to velocity.

## 4. What to animate

- Animate `transform` and `opacity` (GPU-friendly). Also fine when smooth: `filter: blur`, `clip-path`, `backdrop-filter` (sparingly, costly), color.
- Avoid animating `width`, `height`, `top`, `left`, `margin` (layout thrash). Use transform, or FLIP / View Transitions API / `grid-template-rows: 0fr → 1fr` for expanding.
- Never `transition: all`; list properties.
- Start from a visible state: content must be readable even if JS/animation never runs (no `opacity: 0` waiting for a scroll trigger that may not fire).
- Stagger lists lightly (≤ 6 items animated; the rest appear).
- One authored moment per page, not the same fade-up on every section.

## 5. Reduced motion (required)

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important; animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important; scroll-behavior: auto !important;
  }
}
```
Better: design a reduced variant (cross-fade instead of slide; no parallax; no autoplaying video). Never auto-play motion longer than 5s without a pause control (WCAG 2.2.2). Nothing flashes more than 3 times per second.

## 6. Tools

- CSS transitions/keyframes and the View Transitions API for most UI.
- Motion (Framer Motion) for React component orchestration and layout animations.
- GSAP + ScrollTrigger for complex scroll-driven marketing sequences (the `web-motion` skill covers it).
- Native: SwiftUI `withAnimation`/`matchedGeometryEffect`, Compose `animate*AsState`, Reanimated on React Native.
- Lottie/Rive for illustrated animations; keep files small.

## 7. Performance checks

- 60fps on a mid-range phone (Chrome DevTools performance panel, CPU 4× slowdown).
- No layout shift caused by animation (CLS).
- Pause off-screen animations (IntersectionObserver), stop loops when the tab is hidden.
- `will-change` only on elements about to animate, removed after.
