---
name: email-notifications
description: Load before adding email, push, SMS/WhatsApp or in-app notifications, or when email lands in spam. SPF/DKIM/DMARC, providers, RTL templates, unsubscribe, queues, OTP, preferences. Triggers: email, push, SMS, إشعارات, الإيميلات تروح سبام.
---

# Email and Notifications

Notifications are part of the product: a password reset that lands in spam is a broken login, a receipt in the wrong direction is a broken brand, a push storm gets the app uninstalled. Authenticate the domain, send through a provider, render for every client and language, respect preferences, and handle the feedback loop (bounces, complaints, unsubscribes).

| File | Use it for |
|------|-----------|
| `references/messaging.md` | Email setup (DNS, subdomains, providers), Gmail/Yahoo sender requirements, templates and RTL email, sending architecture (queue/outbox), bounces/complaints, marketing vs transactional, push (APNs/FCM/Expo), SMS/WhatsApp/OTP, in-app notification center, preferences, testing |
| `scripts/check-email-dns.sh` | Check a domain's MX, SPF, DMARC, common DKIM selectors, BIMI and MTA-STS, with pass/warn output |

## 1. Rules

1. **Send from your own domain through a provider** (Resend, Postmark, SES, SendGrid, Mailgun), never from a personal mailbox or the server's sendmail.
2. **Authenticate**: SPF (one record, ≤ 10 lookups), DKIM (provider keys), DMARC (start `p=none` with reports, move to `quarantine`/`reject`), aligned From domain (`launch-security` B7). Run `check-email-dns.sh <domain>`.
3. **Separate streams**: transactional (`mail.example.com` / provider transactional stream) and marketing (`news.example.com`) so a marketing complaint spike doesn't block password resets.
4. **Marketing needs consent and one-click unsubscribe** (`List-Unsubscribe` + `List-Unsubscribe-Post: List-Unsubscribe=One-Click`), honored quickly; transactional mail has no marketing content.
5. **Send asynchronously** through a queue/outbox with retries; never block a request on SMTP/API latency; idempotency so retries don't double-send.
6. **Handle feedback**: bounce and complaint webhooks → suppress the address; track delivery, opens/clicks only where consented.
7. **Templates in code** (React Email / MJML), localized per recipient, RTL for Arabic, plain-text part, tested in major clients, dark-mode safe.
8. **Respect people**: preferences per channel and category, quiet hours/time zones, batching/digests, frequency caps; security-critical messages (reset, new login) always sent.
9. **No secrets or sensitive data in messages**: links with short-lived single-use tokens (`launch-security` 17), no full card numbers, minimal personal data in push previews.
10. **Measure**: delivery rate, bounce rate, spam complaint rate (keep < 0.1%, never ≥ 0.3%), push opt-in and open rates, unsubscribe rate.

## 2. Workflow

1. Pick provider; set up sending domain/subdomain; add DNS records; verify with `check-email-dns.sh`.
2. Build `notifications/` module: `send(userId, type, data)` → resolve preferences + locale → render template → enqueue per channel.
3. Templates for: verify email, magic link/OTP, password reset, new device login, welcome, receipt/invoice, payment failed, trial ending, invitations, digests.
4. Webhooks: delivered/bounced/complained → update suppression list and logs.
5. Push: permission pre-prompt at the right moment, token registration per device, server sends via APNs/FCM/Expo, handle invalid tokens.
6. Preferences page + unsubscribe links; quiet hours by user time zone.
7. Test: rendering (Litmus/Email on Acid or manual in Gmail/Outlook/Apple Mail, light/dark, ar/en), spam score (mail-tester), links, unsubscribe, bounces.

## 3. Done when

- [ ] SPF, DKIM, DMARC pass (aligned); `check-email-dns.sh` has no FAIL.
- [ ] Transactional and marketing separated; one-click unsubscribe on marketing.
- [ ] Sending via queue with retries and idempotency; bounces/complaints suppress addresses.
- [ ] Templates localized (Arabic RTL correct), plain-text part, tested in major clients and dark mode.
- [ ] Preferences respected per channel/category; quiet hours; security emails always sent.
- [ ] Push permission requested in context; invalid tokens cleaned; payloads contain no sensitive data.
