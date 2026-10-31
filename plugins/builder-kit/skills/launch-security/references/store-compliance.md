# App Store & Google Play compliance: checks S1–S10

Apply SKILL.md §1 "Rules of work". Run these for any app shipped to the Apple App Store or Google Play (native, React Native, Expo, Flutter, Capacitor, wrapped web apps). Store rules change often: before submitting, re-read the current [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) and Google Play policy pages and flag anything that differs from this file.

Rejections cost days per round. Each item below is a frequent real-world rejection cause.

---

## S1 · Digital purchases use the store's billing · CRITICAL (rejection)

- Digital goods, features, content or subscriptions consumed **inside the app** (premium plans, credits, unlocks, AI usage) must be sold through **Apple In-App Purchase / StoreKit** and **Google Play Billing**. Do not run Stripe, PayPal, MyFatoorah, Moyasar, Tap or any web checkout inside the app for these.
- Physical goods and real-world services (deliveries, rides, bookings) use normal payment providers. IAP is not allowed for them.
- External purchase links: allowed in the **US storefront** without an entitlement (2025 court ruling). In every other storefront, no buttons, links or calls to action that steer to outside purchasing, unless the app holds a StoreKit External Purchase entitlement Apple grants for that region. Confirm the current rule for each target storefront before shipping.
- "Reader" apps (content bought elsewhere) and multiplatform services have specific exceptions. Check guideline 3.1.3 before relying on one.
- **Security tie-in (check 19):** never unlock based on the client saying "purchase succeeded". Verify every transaction on the server: Apple App Store Server API + App Store Server Notifications V2 (signed JWS, verify the chain); Google Play Developer API (`purchases.subscriptionsv2`) + Real-time Developer Notifications. Store entitlements server-side; handle renewals, refunds, revocations, grace periods and billing retry. RevenueCat or similar is fine, but its webhook must be authenticated.

**Done when**
- [ ] Every in-app digital sale goes through IAP / Play Billing.
- [ ] No external purchase steering outside the storefronts where it is allowed.
- [ ] Purchases verified server-side; refunds and expiry remove access.

---

## S2 · Paywall and subscription disclosures · HIGH (rejection)

On every paywall / purchase screen:
- Links to the **Privacy Policy** and **Terms of Use (EULA)**, working and reachable without signing in. Also set them in App Store Connect / Play Console.
- Clear title, **price and billing period** per plan, what is included, and that it **auto-renews** unless cancelled. Free trial length and what is charged after it.
- A **Restore Purchases** button (iOS).
- How to cancel / manage the subscription (link to the system subscription settings).
- No misleading UI: the price must be the most prominent number; no hidden close button; no fake countdowns.

**Done when**
- [ ] Privacy Policy and Terms links are visible on the paywall and in store metadata.
- [ ] Price, period, auto-renewal, and trial terms are shown before purchase.
- [ ] Restore Purchases exists and works.

---

## S3 · In-app account deletion · CRITICAL (rejection)

- If the app allows account creation, users must be able to **start account deletion from inside the app** (usually Settings → Account → Delete account). Apple guideline 5.1.1(v); Google Play also requires an in-app path **and** a public web URL for deletion requests (declared in the Data safety form).
- Deletion means deletion: deactivation, "freeze" or hiding does not count. Delete or anonymize the user's data across the database, storage and third parties (B6). Disclose anything retained for legal/fraud reasons and for how long.
- Confirm with re-authentication (check 16 high-risk actions), then revoke all sessions and tokens.
- Sign in with Apple users: revoke the Apple token via the REST API on deletion.
- Remind users with active store subscriptions that deletion doesn't cancel billing; link to subscription management.

**Done when**
- [ ] A delete-account action exists in-app and (for Google Play) on the web.
- [ ] Deletion removes or anonymizes data everywhere, and sessions are revoked.
- [ ] Retained data is disclosed.

---

## S4 · Privacy policy, labels and manifests · HIGH (rejection)

- A real, app-specific privacy policy URL (not a generic template that contradicts what the app does). Linked in the app and both store listings.
- **Apple privacy nutrition labels** and **Google Play Data safety form** must match what the app and every SDK actually collect and share. Audit SDKs (analytics, ads, crash reporting, auth, AI) and declare their data too.
- **Apple privacy manifest** (`PrivacyInfo.xcprivacy`): declare collected data types, tracking domains, and "required reason" API usage (e.g. UserDefaults, file timestamps, system boot time, disk space). Third-party SDKs on Apple's list must ship their own signed manifests.
- **App Tracking Transparency:** if the app tracks users across other companies' apps/sites (ads attribution, IDFA), show the ATT prompt first and respect a refusal.

**Done when**
- [ ] Privacy policy is accurate and linked everywhere.
- [ ] Nutrition labels / Data safety form match real collection, including SDKs.
- [ ] Privacy manifest is present and complete; ATT is used if tracking.

---

## S5 · Sign-in rules · HIGH (rejection)

- If the app offers third-party or social login (Google, Facebook…) as the primary account, Apple requires also offering **Sign in with Apple** or another login option that meets guideline 4.8 (limits data to name and email, lets users hide their email, no ad tracking without consent). Check the current wording.
- Don't force account creation for features that don't need an account (guideline 5.1.1).
- Login must work for the reviewer: provide a **demo account** (with any 2FA disabled for it, or instructions) in review notes.

---

## S6 · Permissions and purpose strings · MEDIUM (rejection)

- Request permissions (camera, mic, location, photos, contacts, notifications, Bluetooth, tracking) only when the feature needs them, at the moment of use.
- iOS `Info.plist` usage descriptions (`NSCameraUsageDescription`, etc.) must explain specifically why, in every app language.
- Android: request only needed permissions; sensitive ones (background location, SMS, call log, all-files access, exact alarms, accessibility) need a Play Console declaration and a core-feature justification.
- Never block the app because a non-essential permission was denied.

---

## S7 · User-generated content & safety · HIGH (rejection, if applicable)

Apps with UGC, chat or social features need: content filtering, a way to **report** content, a way to **block** users, a published contact method, and timely moderation. AI-generated content counts as content: filter it and allow reporting.

---

## S8 · Completeness and quality · MEDIUM (rejection)

- No crashes, placeholder text, "coming soon" or broken links. Every button does something.
- The app must work on the reviewer's device and network, including IPv6-only networks.
- Metadata (name, screenshots, description) matches the actual app; no other platform's name or prices in screenshots.
- Minimum functionality: not a thin wrapper around a website (guideline 4.2). Add real native value if it's a web app.
- Age rating answers are accurate. Kids category apps follow the extra kids rules (no third-party analytics/ads without strict compliance).

---

## S9 · Google Play technical requirements · MEDIUM

- Target the current required **target API level** (Google raises it yearly; check Play Console before each release).
- Use Play App Signing; keep the upload key safe and backed up.
- Data safety form complete; account deletion URL set.
- Use the Play Integrity API for sensitive actions if abuse is a risk (see platforms.md).

---

## S10 · Review submission hygiene · LOW

- Review notes: demo account, how to reach every paid/hidden feature, why each sensitive permission is needed, and any region/entitlement details.
- Reply to rejections in Resolution Center with specifics; fix the root cause in all similar places, not only the screen named.
- Keep a `STORE_CHECKLIST.md` in the repo with S1–S10 ticked before every submission.
