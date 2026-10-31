# Messaging reference

## 1. Email DNS setup

| Record | Example | Notes |
|--------|---------|-------|
| SPF (TXT on sending domain) | `v=spf1 include:amazonses.com include:_spf.google.com -all` | One SPF record only; ≤ 10 DNS lookups; `-all` or `~all` |
| DKIM (TXT/CNAME) | `resend._domainkey.mail.example.com` → provider key | Provider gives selector + key; 2048-bit |
| DMARC (TXT `_dmarc`) | `v=DMARC1; p=none; rua=mailto:dmarc@example.com; adkim=s; aspf=s` | Start `p=none`, read reports 2–4 weeks, then `p=quarantine`, then `p=reject` |
| Return-Path / bounce (CNAME/MX) | per provider | Enables SPF alignment |
| MX (receiving) | your mail host | Needed for replies and DMARC reports |
| BIMI (TXT `default._bimi`) | `v=BIMI1; l=https://…/logo.svg; a=…` | Optional; needs DMARC enforcement (and VMC/CMC for Gmail logo) |
| MTA-STS / TLS-RPT | `_mta-sts`, `_smtp._tls` | Optional hardening for inbound |

Use a subdomain for sending (`mail.example.com`, `news.example.com`) to isolate reputation. Warm up new domains/IPs gradually.

Bulk sender requirements (Gmail and Yahoo, since 2024, for senders of ~5,000+/day to their users): SPF and DKIM, DMARC published (at least `p=none`) with From alignment, one-click unsubscribe for marketing, spam rate below 0.3% (aim < 0.1%), valid forward/reverse DNS, TLS.

## 2. Providers

| Need | Good options |
|------|--------------|
| Transactional, developer-first | Resend, Postmark, AWS SES (cheapest at scale), SendGrid, Mailgun |
| Marketing/newsletters | Provider's broadcast feature, Loops, Customer.io, Brevo, Mailchimp, Kit |
| Lifecycle automation (behavior-triggered) | Customer.io, Loops, Braze (large) |
| Inbound email parsing | Postmark, SendGrid, Mailgun inbound, SES receiving |

## 3. Templates

- React Email or MJML → HTML with tables, inline styles; plus a plain-text alternative.
- Width ~600px, single column on mobile, 14–16px text, buttons as styled links (bulletproof buttons), alt text on images, no critical info in images.
- Dark mode: avoid pure white logos on transparent backgrounds; test with forced dark (Gmail/Outlook invert colors); use `color-scheme` meta and dark-specific styles where supported.
- Arabic: `<html dir="rtl" lang="ar">`, `dir="rtl"` and `align="right"` on tables/cells, `text-align:right` inline (some clients ignore `dir`), Arabic web font with system fallbacks (Tahoma/Arial render Arabic in most clients), test in Gmail web/app, Outlook desktop, Apple Mail.
- Localize subject, preheader, body, dates/currency (`i18n-rtl` §6) from the recipient's locale.
- Links: absolute HTTPS URLs on your domain; UTM only on marketing; single-use tokens with short expiry for auth links.

## 4. Sending architecture

```
app code → notifications.send(userId, "invoice.paid", data)
   → preferences + locale + suppression check
   → outbox row (same DB transaction as the business change)
   → worker: render template → provider API (idempotency key = outbox id) → store provider message id
   → provider webhooks: delivered / bounced / complained / opened / clicked → update status, suppression list
```
- Outbox ensures "order saved but email never sent" can't happen and retries are safe.
- Rate limit per recipient (no more than N per hour per type) to avoid loops.
- Log message type, recipient ID (not full address in shared logs), provider ID, status.

## 5. Bounces, complaints, suppression

- Hard bounce (invalid address): suppress permanently.
- Soft bounce (mailbox full, temporary): retry by provider; suppress after repeated soft bounces.
- Complaint (marked as spam): suppress from marketing immediately; review content/frequency.
- Verify addresses at signup (double opt-in for marketing; email verification for accounts); block disposable domains if abuse appears.

## 6. Push notifications

- **Expo**: `expo-notifications` → Expo push tokens → Expo Push API (handles APNs/FCM); check receipts and remove `DeviceNotRegistered` tokens.
- **Native**: APNs (token-based auth .p8 key) for iOS, FCM HTTP v1 for Android/web.
- **Web push**: service worker + VAPID keys; ask permission after a user action, never on page load; iOS supports web push only for installed home-screen web apps.
- Permission: pre-prompt explaining the value ("Get notified when your order ships"); ask at the relevant moment; settings to manage categories.
- Payloads: no sensitive data in the visible preview (bank balances, health info, OTPs on lock screen unless the user chose it); deep link to the right screen; localized text; badge counts accurate.
- Android notification channels per category; iOS interruption levels (passive/active/time-sensitive) used honestly.

## 7. SMS, WhatsApp, OTP

- Providers: Twilio, Vonage, MessageBird/Bird, Unifonic (Gulf), Infobip; WhatsApp Business Platform (Cloud API) with pre-approved templates.
- Sender ID registration rules differ by country (e.g. Saudi Arabia and UAE require registered sender IDs); plan lead time.
- OTP: 6 digits, 5–10 minute expiry, single use, rate limited per number and per IP, `autocomplete="one-time-code"` on web and platform SMS retrieval APIs on Android; consider passkeys or email magic links to reduce SMS cost and SIM-swap risk.
- SMS pumping fraud: restrict destination countries, rate limit, CAPTCHA/attestation on abuse, monitor cost per country.

## 8. In-app notification center

- Table: `notifications(id, user_id, type, title, body, data jsonb, read_at, created_at)`; index `(user_id, read_at, created_at desc)`.
- Real-time via Supabase Realtime/websockets/SSE; badge count; mark read/all read; deep links; retention (e.g. 90 days).
- Or hosted: Knock, Novu, Courier, MagicBell (multi-channel orchestration + preferences UI).

## 9. Preferences and law

- Preferences per category × channel (email/push/SMS), defaults sensible, security/transactional always on.
- Quiet hours by user time zone; digest instead of many single messages.
- Consent records for marketing (when, how, what text); unsubscribe within days (laws: CAN-SPAM, GDPR/ePrivacy, CASL, local telecom rules).
- Footer for marketing: physical address where required, unsubscribe link, why they receive it.

## 10. Testing

- Local capture: Mailpit/MailHog, provider sandbox mode, React Email preview.
- Rendering tests in Gmail (web/iOS/Android), Outlook (Windows/Mac/web), Apple Mail, in light/dark, ar/en.
- Spam check: mail-tester.com score ≥ 9/10; check headers for SPF/DKIM/DMARC pass.
- E2E: Playwright + a test inbox API (Mailosaur, Mailpit API) to click verification/reset links.
- Push: Expo push tool / Firebase console test messages; verify deep links.
