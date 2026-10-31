---
name: payments-billing
description: Take money correctly - one-off payments, subscriptions, trials, plans and entitlements, upgrades/downgrades with proration, coupons, taxes/VAT, invoices and receipts, failed payments and dunning, refunds and disputes, marketplaces/payouts, regional methods (Apple Pay, Google Pay, mada, STC Pay, BNPL like Tabby/Tamara) and in-app purchases (StoreKit 2, Google Play Billing, RevenueCat) - with server-side pricing, verified idempotent webhooks as the source of truth, reconciliation and test clocks. Use when adding checkout, pricing, plans, paywalls, subscriptions, credits, or anything that charges users; when integrating Stripe, Paddle, Lemon Squeezy, Moyasar, Tap, HyperPay, Checkout.com, RevenueCat; or when the user says payments, billing, subscription, checkout, الدفع, الاشتراكات, بوابة دفع, باقات.
---

# Payments and Billing

Money bugs are the most expensive bugs: they lose revenue silently, give away paid features, double-charge customers and invite chargebacks and store rejections. The core design: **the provider is the source of truth for payment state, webhooks update your database, your database grants entitlements, and the client never decides anything about price or access.**

| File | Use it for |
|------|-----------|
| `references/billing.md` | Choosing a provider/model, data model (customers, subscriptions, entitlements, ledger), checkout flows, webhooks and the events to handle, subscription lifecycle, proration, trials, coupons, tax, invoices, dunning, refunds/disputes, credits/usage billing, marketplaces, Gulf/regional methods, in-app purchases, testing, reconciliation, pricing page |

Security checks for payments live in `launch-security` 19 (prices/payments), P12 (webhook pattern), S1–S2 (store purchase rules). Follow them; `security_scan.py` flags unsigned webhooks.

## 1. Rules

1. **Server computes the price** from your product catalog (or the provider's price IDs). The client sends what it wants (plan ID, quantity), never amounts.
2. **Hosted checkout by default** (Stripe Checkout/Elements, Paddle, provider-hosted pages): card data never touches your servers, PCI scope stays minimal (SAQ A).
3. **Webhooks are the source of truth.** Verify the signature on the raw body, dedupe by event ID, process idempotently, respond 2xx fast, do heavy work in a job. The success redirect is only UX: it never grants access by itself.
4. **Entitlements are explicit**: a table (or provider entitlements) that says what each customer can use now. Feature checks read entitlements, never "has a Stripe subscription object".
5. **Every state is handled**: trialing, active, past_due, unpaid, canceled (at period end vs immediately), paused, incomplete, refunded, disputed.
6. **Money in integer minor units + currency**, totals computed once, server-side; rounding rules explicit; taxes from the provider or a tax engine.
7. **Idempotency keys** on every create call to the provider; unique constraints on provider IDs in your DB.
8. **Store rules for apps**: digital goods inside iOS/Android apps use StoreKit / Play Billing unless a specific, current exception applies (`launch-security` S1–S2). Physical goods and real-world services use normal payments.
9. **Customers can manage and cancel easily** (customer portal), receive receipts/invoices with required tax details, and get clear failed-payment emails.
10. **Reconcile.** A daily job compares provider records with your DB (subscriptions, entitlements, payments) and alerts on drift.

## 2. Workflow

1. Decide the model from the spec: one-off, subscription (per seat / tiered / usage-based), credits, marketplace; merchant of record or not (`billing.md` §1).
2. Model data (`billing.md` §2) and plan catalog (in provider + mirrored config).
3. Build checkout (hosted), webhooks handler (verified, idempotent, job queue), entitlement updates, customer portal link.
4. Gate features with `hasEntitlement(user, 'feature')`.
5. Handle lifecycle emails (receipt, trial ending, payment failed, canceled) (`email-notifications`).
6. Test in test mode with test clocks: every event and state transition, duplicates, out-of-order events, failed cards, 3DS, refunds, disputes (`billing.md` §11).
7. Launch checklist (`billing.md` §13).

## 3. Done when

- [ ] No client-supplied amounts; prices from server catalog; tampering tests fail safely.
- [ ] Webhook signature verified on raw body; event dedupe table; idempotent handlers; retries safe.
- [ ] Entitlements table drives access; every subscription state mapped.
- [ ] Customer portal or equivalent for card update and cancel; receipts/invoices sent.
- [ ] Dunning: failed payment emails, retries, grace period, downgrade on final failure.
- [ ] Tests cover lifecycle with test clocks; reconciliation job running; alerts on webhook failures.
- [ ] Tax/VAT handled for the countries you sell to; legal pages updated (refund policy, terms).
