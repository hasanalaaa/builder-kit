# Native apps: iOS and Android

Native users expect native behavior. Brand lives in color, type, imagery and motion; structure follows the platform.

## 1. iOS (Human Interface Guidelines)

- **Navigation**: tab bar (2–5 tabs) at the bottom; `NavigationStack` with large titles on root screens; back swipe from the leading edge must always work.
- **Controls**: system components first (`List`, `Form`, `Toggle`, `Picker`, `DatePicker`, `Menu`, `ShareLink`, sheets with detents). Custom controls only when they clearly add value.
- **Touch targets**: ≥ 44×44pt.
- **Type**: SF Pro via system font with **Dynamic Type** text styles (`.body`, `.headline`, `.largeTitle`); custom fonts must scale (`.font(.custom(_, size:, relativeTo:))`). Test at the largest accessibility size.
- **Color**: semantic system colors (`.primary`, `.secondary`, `Color(.systemBackground)`) or asset-catalog colors with Any/Dark appearances. Support Increase Contrast.
- **Layout**: respect safe areas; leading/trailing (not left/right) so RTL works automatically; standard margins (16–20pt).
- **Sheets**: `.sheet` with `.presentationDetents([.medium, .large])` for options; full-screen cover for immersive creation.
- **Feedback**: haptics (`.sensoryFeedback` / `UIImpactFeedbackGenerator`) for meaningful moments, not every tap.
- **Icons**: SF Symbols with matching weight to text; they mirror automatically for directional symbols in RTL.
- **Materials**: system materials for overlays; Liquid Glass/translucency only through system components and only over content.
- **Permissions**: pre-prompt screen explaining value before the system dialog; handle "denied" gracefully with a Settings link.
- **Widgets, Live Activities, App Intents/Shortcuts** when the product has glanceable or repeatable actions.

## 2. Android (Material 3)

- **Navigation**: navigation bar (3–5) on phones, navigation rail on tablets/foldables, drawer for many destinations; system back (predictive back gesture) must work everywhere.
- **Components**: Material 3 components in Compose (`Scaffold`, `TopAppBar`, `NavigationBar`, `ModalBottomSheet`, `Snackbar`, `FloatingActionButton` when one action dominates).
- **Touch targets**: ≥ 48×48dp.
- **Type**: Material type scale (display/headline/title/body/label), respects user font size (sp units).
- **Color**: Material color roles (primary, onPrimary, surface, surfaceContainer…); support dynamic color (Material You) where brand allows, with a brand fallback scheme.
- **Edge-to-edge**: draw behind system bars, handle insets (`WindowInsets`).
- **Layout**: adaptive layouts for compact/medium/expanded window sizes; start/end (RTL-ready).
- **Feedback**: ripple on press, snackbars with action for undo.
- **Permissions**: request in context, explain, handle "don't ask again".

## 3. Cross-platform (Expo / React Native / Flutter)

- Use platform-adaptive components (e.g. native stack, platform date pickers, `ActionSheetIOS` vs bottom sheet) rather than one design forced on both.
- Keep one token set; map to platform roles.
- Respect `I18nManager.isRTL` (RN) / `Directionality` (Flutter); test RTL on device — RN requires an app reload to switch direction.
- Font scaling on: `allowFontScaling` stays true; layouts survive 200% text.
- Use `react-native-safe-area-context`; keyboard avoiding on forms; `Pressable` with hit slop for small icons.
- Animations on the UI thread (Reanimated); 60fps on mid-range Android.

## 4. Store-facing design

- App icon: simple silhouette, no text, readable at small sizes, platform templates (iOS no transparency; Android adaptive icon layers).
- Screenshots: show real UI with a one-line benefit caption per screen, localized for Arabic with RTL screens.
- Launch screen: brand color + logo, no loading text, matches the first screen to feel instant.
- See `mobile-release` for store listing and review requirements.
