# Mobile release reference

Store requirements change several times a year. Check Apple's App Review Guidelines and Google Play policy center before each major release.

## 1. Identity and versioning

| Item | iOS | Android | Expo config |
|------|-----|---------|-------------|
| Permanent ID | Bundle ID | applicationId | `ios.bundleIdentifier`, `android.package` |
| User-facing version | CFBundleShortVersionString | versionName | `version` |
| Build number (must increase) | CFBundleVersion | versionCode | `ios.buildNumber`, `android.versionCode` or EAS `autoIncrement` + `appVersionSource: "remote"` |
| Display name | CFBundleDisplayName | app label | `name` (localize with `locales`) |

## 2. Signing

- iOS: distribution certificate + provisioning profile; let EAS manage (`eas credentials`) or Xcode automatic signing; App Store Connect API key for CI.
- Android: Play App Signing (Google holds the app signing key); you keep the upload key (backed up, password in a secret manager).
- Never commit keystores/p12/p8 files; rotate if leaked (`launch-security` 24–25).

## 3. EAS (Expo)

```json
// eas.json
{
  "cli": { "appVersionSource": "remote" },
  "build": {
    "development": { "developmentClient": true, "distribution": "internal" },
    "preview": { "distribution": "internal", "channel": "preview" },
    "production": { "autoIncrement": true, "channel": "production" }
  },
  "submit": { "production": { "ios": { "ascAppId": "<id>" }, "android": { "track": "internal" } } }
}
```
- `eas build --profile production --platform all`, `eas submit`, `eas update --channel production --message "…"`.
- `runtimeVersion` policy (`"policy": "appVersion"` or `"fingerprint"`) so OTA updates only reach compatible native builds.
- Environment variables per profile in EAS (secrets not in `app.config`).

## 4. Permissions and usage strings

| Capability | iOS key (Info.plist) | Android permission | Notes |
|------------|----------------------|--------------------|-------|
| Camera | NSCameraUsageDescription | CAMERA | |
| Photos (read) | NSPhotoLibraryUsageDescription | READ_MEDIA_IMAGES (13+) or Photo Picker (no permission) | Prefer system photo picker |
| Save photos | NSPhotoLibraryAddUsageDescription | — | |
| Microphone | NSMicrophoneUsageDescription | RECORD_AUDIO | |
| Location (in use) | NSLocationWhenInUseUsageDescription | ACCESS_FINE/COARSE_LOCATION | |
| Location (background) | NSLocationAlwaysAndWhenInUseUsageDescription | ACCESS_BACKGROUND_LOCATION | Strong justification; Play declaration form |
| Contacts | NSContactsUsageDescription | READ_CONTACTS | |
| Calendar | NSCalendarsFullAccessUsageDescription / WriteOnly | READ/WRITE_CALENDAR | |
| Face ID | NSFaceIDUsageDescription | USE_BIOMETRIC | |
| Tracking (ATT) | NSUserTrackingUsageDescription | — (AD_ID permission for ad ID) | Only if you track across apps/websites |
| Bluetooth | NSBluetoothAlwaysUsageDescription | BLUETOOTH_CONNECT/SCAN | |
| Motion | NSMotionUsageDescription | ACTIVITY_RECOGNITION | |
| Notifications | (runtime prompt) | POST_NOTIFICATIONS (13+) | |

Usage strings: specific benefit ("Rawdah uses your camera to share photos of today's activities with parents"), localized (`InfoPlist.strings` / Expo `locales`), never generic ("This app needs access"). Request at the moment of use with a pre-prompt; handle denial gracefully with a Settings link.

Play policy-sensitive permissions (need declarations or are restricted): SMS/Call Log, `QUERY_ALL_PACKAGES`, `MANAGE_EXTERNAL_STORAGE`, background location, accessibility services, exact alarms, full-screen intent.

## 5. Privacy

- **iOS Privacy Manifest** (`PrivacyInfo.xcprivacy`): declare collected data types, tracking domains, and reasons for "required reason APIs" (UserDefaults, file timestamps, disk space, system boot time, active keyboards). Expo: `ios.privacyManifests` in config; third-party SDKs must ship their own manifests (keep SDKs updated).
- **App Privacy labels** (App Store Connect) and **Data safety** (Play Console): list data collected/shared by you and SDKs (analytics, crash reporting, ads, auth); keep in sync with the privacy policy (`legal-compliance`).
- **ATT**: show the system prompt before any tracking/IDFA access; don't gate features on consent; pre-prompt allowed but no incentives.
- **Account deletion**: in-app path for apps with account creation (both stores); Play also requires a web link to request deletion.

## 6. Common rejection causes (and fixes)

| Cause | Fix |
|-------|-----|
| Crashes/bugs on review device | Test on latest OS and older supported devices; reviewer uses fresh install; no dev servers |
| Login required but no demo account | Provide demo credentials and notes; or allow guest browsing |
| Incomplete metadata, placeholder content | Real screenshots, real text, working links |
| Digital goods sold without IAP | Use StoreKit/Play Billing; follow current storefront exceptions (`launch-security` S1–S2) |
| Missing account deletion | Add in-app deletion |
| Third-party login without Sign in with Apple (when required) | Add Sign in with Apple or meet an exception (guideline 4.8) |
| Vague permission strings | Specific, localized usage descriptions |
| Minimum functionality / web wrapper | Native value: offline, push, device features, native navigation |
| UGC without moderation | Report, block, filter, terms acceptance (S9) |
| Privacy label mismatch | Audit SDKs; update labels |
| Hidden features / OTA changing purpose | Keep OTA to fixes and minor changes; submit new features for review |

## 7. OTA updates (EAS Update / CodePush alternatives)

- Allowed for JS/asset fixes and improvements that don't change the app's primary purpose; native code changes require a store release.
- Channels: `preview` → test → `production`; roll out gradually (`eas update --rollout-percentage`) and roll back (`eas update:rollback` / republish previous).
- `runtimeVersion` prevents incompatible bundles; test the update on a build from the store track.

## 8. Rollout and monitoring

- iOS phased release (7 days, pausable) and Play staged rollout (e.g. 5% → 20% → 50% → 100%).
- Watch: crash-free users/sessions, ANR rate (Play vitals thresholds affect visibility), reviews mentioning the new version, key funnels, backend errors from the new app version.
- Halt rollout on regressions; hotfix via OTA if JS-only, else expedited review (iOS, sparingly).

## 9. Forced and soft update

- `GET /v1/config` returns `minSupportedVersion` and `latestVersion` per platform; app compares on launch/foreground.
- Below minimum → blocking screen with store link; below latest → dismissible banner.
- Keep the API backward compatible for supported versions.

## 10. Deep links

- iOS Universal Links: `apple-app-site-association` on your domain (served as JSON, no redirect), Associated Domains entitlement.
- Android App Links: `assetlinks.json` with SHA-256 of the app signing key (Play App Signing key, not the upload key), `autoVerify` intent filters.
- Expo Router handles routes; test cold start and warm start links; fallback web pages.

## 11. Push notifications

- iOS: Push capability + APNs key (.p8) in EAS/Firebase; Android: FCM v1 credentials (service account) in EAS; request permission in context (`email-notifications` §6).
- Test on real devices (simulators have limits), in foreground/background/killed states.

## 12. Store listing (both languages)

- Name (≤ 30 chars iOS), subtitle/short description, keywords (iOS keyword field), long description with benefits first.
- Screenshots: real UI at the device sizes App Store Connect and Play Console currently require; Arabic screenshots show the RTL UI; first 2–3 screenshots carry the value proposition.
- App preview video optional; feature graphic for Play.
- Category, age rating questionnaire, content rights, support URL, marketing URL, privacy policy URL.
- Localize per storefront (Arabic for Gulf/Egypt storefronts).

## 13. Release checklists

**Before first submission**
- [ ] Bundle/application IDs final; icons (no transparency on iOS, adaptive icon on Android), splash, display name localized.
- [ ] Permissions minimal with localized usage strings; privacy manifest; privacy labels/Data safety; ATT if tracking.
- [ ] Account deletion, Sign in with Apple (if required), IAP for digital goods, restore purchases.
- [ ] Crash reporting with dSYMs/mappings; analytics consent.
- [ ] Deep links verified; push working; offline behavior acceptable.
- [ ] Demo account + review notes; support and privacy URLs live.
- [ ] Tested on oldest supported OS and smallest screen, Arabic and English, dark mode, Dynamic Type/large fonts.

**Every release**
- [ ] Version + build bumped; "What's new" in both languages.
- [ ] `mobile_release_check.py` 0 ERROR; tests green; TestFlight/internal smoke test.
- [ ] Phased/staged rollout; crash-free and reviews watched for 48h.
