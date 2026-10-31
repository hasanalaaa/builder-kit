---
name: mobile-release
description: Load before an App Store or Google Play submission, update or after a rejection. Identity, signing, EAS, TestFlight/Play tracks, permissions, privacy manifest, review traps, OTA, rollouts. Triggers: App Store, Google Play, TestFlight, رفع التطبيق, رفض أبل.
---

# Mobile Release

Store releases are slow to fix: a rejected build costs days, a crashing release stays on phones until users update, and a wrong privacy label can pull the app. Prepare the release like a checklist-driven launch: identity, signing, permissions, privacy, listing, testing tracks, staged rollout, and monitoring.

| File | Use it for |
|------|-----------|
| `references/release.md` | Identity/versioning, signing, EAS Build/Submit/Update, TestFlight and Play tracks, listing assets, permissions and usage strings, privacy manifest and labels, common rejection causes, OTA rules, staged rollout, forced update, deep links, push, post-release monitoring, checklists |
| `scripts/mobile_release_check.py` | Check Expo `app.json`/`app.config.*`, `eas.json`, iOS `Info.plist` and Android manifest: bundle IDs, versions/build numbers, icon/splash, usage strings for each installed permission module, privacy manifest, risky Android permissions, Sign in with Apple requirement, updates runtime version |

Store policy rules (IAP, account deletion, privacy labels, ATT, Sign in with Apple, UGC) live in `launch-security/references/store-compliance.md` S1–S10. Design conventions in `design-system/references/native.md`.

## 1. Rules

1. **Identity is permanent**: bundle ID / application ID chosen once (`com.company.app`), never changed after release.
2. **Every build has a unique, increasing build number**; marketing version follows semver (`1.4.0`). Automate (EAS `autoIncrement`, fastlane, CI).
3. **Signing credentials are secrets**: managed by EAS/App Store Connect API keys/Play App Signing; backed up; never committed.
4. **Permissions are asked only when needed**, with honest usage strings that explain the user benefit, in every supported language.
5. **Privacy disclosures match reality**: App Privacy labels, Data safety form, `PrivacyInfo.xcprivacy` (required-reason APIs), ATT prompt only if you track; include third-party SDK behavior.
6. **Test through the real channels**: TestFlight (internal → external) and Play internal → closed → open testing, on real devices, in Arabic and English, on small and large screens, slow networks.
7. **Release gradually**: phased release (iOS 7-day) and staged rollout (Play percentage); watch crash-free rate before expanding; halt on regressions.
8. **OTA updates only for JS/assets** and within store rules (no changing the app's primary purpose, no bypassing review for new features in spirit); native changes need a store build; runtime versions prevent incompatible updates.
9. **Old versions keep working** or are asked to update: API compatibility for installed versions, `minSupportedVersion` + forced-update screen (`api-contracts` §9).
10. **Monitor after release**: crash-free users ≥ 99.5%, ANR rate, reviews, key funnels; respond to reviews.

## 2. Workflow: first submission

1. Accounts: Apple Developer Program (organization account for companies: D-U-N-S), Google Play Console (organization verification; new personal accounts have testing requirements before production).
2. Config: identifiers, versions, icons, splash, permissions, deep links, push entitlements (`release.md` §1–§4); run `python3 <skill>/scripts/mobile_release_check.py .` → 0 ERROR.
3. Build with EAS (`eas build -p all --profile production`) or Xcode/Gradle; submit to TestFlight / Play internal testing (`eas submit`).
4. Store listing in Arabic and English: name, subtitle/short description, description, keywords, screenshots, preview video, privacy policy URL, support URL, age rating, category, contact.
5. Privacy forms, account deletion info, demo account + review notes for reviewers, export compliance (encryption) answers.
6. Internal test → external/closed test with real users → fix → submit for review → phased/staged release.

## 3. Workflow: each update

1. Bump version/build; changelog ("What's new") in both languages.
2. `mobile_release_check.py`; tests; build; TestFlight/internal track smoke test on real devices.
3. Submit; phased/staged rollout; watch crashes and reviews for 48h; expand or halt.
4. OTA hotfixes for JS-only bugs (EAS Update to the matching runtime/channel), with the same testing on a preview channel first.

## 4. Done when

- [ ] `mobile_release_check.py` 0 ERROR.
- [ ] Builds signed via managed credentials; build numbers auto-increment.
- [ ] Permissions requested in context with localized usage strings; privacy labels/Data safety/privacy manifest match SDKs.
- [ ] Listing complete in Arabic and English with real screenshots; demo account and review notes provided.
- [ ] Tested via TestFlight/Play testing on real devices; account deletion, purchases, push and deep links verified.
- [ ] Phased/staged rollout with crash monitoring; forced-update path exists.
