# Billing reference

## 1. Choosing provider and model

| Situation | Choice |
|-----------|--------|
| SaaS selling globally, you want to handle tax yourself | Stripe (Checkout + Billing + Tax + Customer Portal) |
| You want a merchant of record to collect and remit global sales tax/VAT | Paddle, Lemon Squeezy (they are the seller; simpler tax, higher fee) |
| Gulf customers, local cards (mada), local wallets | Regional gateways: Moyasar, Tap, HyperPay, PayTabs, Checkout.com — supporting mada, Apple Pay, STC Pay; BNPL via Tabby / Tamara |
| Digital content/features inside iOS/Android apps | StoreKit 2 / Google Play Billing, optionally RevenueCat to unify |
| Marketplace paying sellers | Stripe Connect (or regional equivalents) with KYC, split payments, payouts |
| Physical goods store | Shopify, or Stripe/regional gateway + order system |

Check provider availability for your business's country and your customers' countries before choosing; not every provider supports every country.

Pricing models: flat subscription, per-seat, tiered, usage-based (metered), credits/prepaid, one-off, freemium + paid tiers, lifetime deals (beware long-term cost).

## 2. Data model

```sql
customers(id, user_id|org_id, provider, provider_customer_id unique, email, country, tax_id, created_at)
subscriptions(id, customer_id, provider_subscription_id unique, plan_id, status, quantity,
              current_period_start, current_period_end, cancel_at_period_end, trial_end, canceled_at, updated_at)
entitlements(id, org_id, feature, limit_value, source ('subscription'|'grant'|'iap'), source_id, starts_at, ends_at)
payments(id, customer_id, provider_payment_id unique, amount_cents, currency, status, refunded_cents, created_at)
billing_events(provider_event_id primary key, type, received_at, processed_at, payload jsonb)  -- webhook dedupe + audit
credit_ledger(id, org_id, delta, reason, ref, balance_after, created_at)  -- for credits/usage; append-only
```
- Plans/features catalog in code/config mapping provider price IDs → plan → entitlements.
- Never derive access from `payments` rows; derive from `entitlements`.

## 3. Checkout flows

**One-off**: server creates Checkout Session with catalog price IDs, `client_reference_id`/metadata = your user/org ID, `success_url`/`cancel_url`; redirect; fulfillment on `checkout.session.completed` (and `payment_intent.succeeded` for async methods).

**Subscription**: Checkout Session in `subscription` mode; trial via `trial_period_days` or trial settings; entitlements on `customer.subscription.created/updated`; customer portal for upgrades/cancel.

**Embedded/Elements**: when you need custom UI; still create intents server-side.

**Apple Pay / Google Pay**: enable in provider; domain verification for Apple Pay on web.

**3-D Secure / SCA**: handled by hosted checkout; for off-session renewals, handle `requires_action` with an email link to complete authentication.

## 4. Webhooks

Handler skeleton: `launch-security/references/secure-patterns.md` P12 (raw body → verify signature → dedupe by event ID → enqueue → 200).

Events to handle (Stripe naming; others are equivalent):
| Event | Action |
|-------|--------|
| `checkout.session.completed` | link customer to user/org; fulfill one-off; for subscriptions wait for subscription events |
| `customer.subscription.created/updated` | upsert subscription; recompute entitlements from status + plan + quantity |
| `customer.subscription.deleted` | end entitlements (or at period end) |
| `invoice.paid` | extend period; record payment; send receipt |
| `invoice.payment_failed` | mark past_due; start dunning emails; keep access during grace period |
| `customer.subscription.trial_will_end` | email 3 days before trial ends |
| `charge.refunded` | adjust entitlements/credits; record refund |
| `charge.dispute.created` | flag account; gather evidence; consider suspending access |
| `payment_intent.succeeded/failed` | for async methods and one-off flows |

Rules: events can arrive late, duplicated or out of order → fetch the latest object from the API when ordering matters, compare timestamps/versions, make every handler idempotent.

## 5. Subscription lifecycle

```
trialing → active → (payment fails) past_due → (retries fail) unpaid/canceled
active → cancel_at_period_end → canceled (at period end)
active ↔ paused (if offered)
```
- Upgrades: immediate with proration (charge the difference now) — usually desired.
- Downgrades: at period end (avoid refunds and abuse), with clear UI.
- Seat changes: prorate; enforce seat limit in app.
- Plan changes update entitlements only after the provider confirms.

## 6. Trials, coupons, credits

- Trial with or without card; one trial per customer (check by email/payment fingerprint/org); remind before conversion.
- Coupons/promotion codes validated by the provider; never accept a client "discount" field.
- Credits: append-only ledger; atomic decrement with a balance check (`data-design` concurrency); refunds add a reversing entry.
- Usage-based: record usage events idempotently; report to provider meters; show current usage and projected bill.

## 7. Tax and invoices

- VAT/GST/sales tax: provider tax calculation (Stripe Tax) or merchant of record; collect billing country (and tax ID for B2B reverse charge).
- Saudi Arabia (ZATCA e-invoicing) and other countries may require specific invoice formats/fields; use a provider or invoicing system that supports local requirements when selling there.
- Invoices/receipts: provider-generated PDFs, sent by email, available in the customer portal; show prices with/without tax per market convention.

## 8. Dunning (failed payments)

- Smart retries in the provider; emails at failure, before final retry, at cancellation; in-app banner with "Update card" (portal link).
- Grace period (e.g. 7–14 days) keeps access; then downgrade to free / read-only, never delete data immediately.
- Card updater and backup payment methods reduce involuntary churn.

## 9. Refunds and disputes

- Refund policy in terms; refunds through provider API with idempotency; adjust entitlements/credits.
- Disputes: respond with evidence (logs of usage, ToS acceptance, delivery); excessive dispute rates risk your account.
- Fraud: provider's risk tools (Radar), velocity limits on signups/trials, block disposable cards for trials if abused.

## 10. In-app purchases

- StoreKit 2: verify transactions with signed JWS (on device + App Store Server API / Server Notifications V2 on your server); `appAccountToken` to link to your user.
- Google Play Billing: verify purchase tokens server-side (Play Developer API), acknowledge purchases within 3 days, handle Real-time Developer Notifications.
- RevenueCat simplifies both + web, with webhooks into your entitlements table.
- Restore purchases button; manage subscription link to the store; price display from the store (localized).
- Follow current store rules for external purchase links and disclosures per storefront (`launch-security` S1–S2).

## 11. Testing

- Provider test mode + test cards (success, decline, insufficient funds, 3DS required, dispute).
- Stripe CLI `stripe listen --forward-to localhost:3000/api/webhooks/stripe` and `stripe trigger <event>`.
- Test clocks to simulate trial end, renewals, failed renewals, cancellations at period end.
- Automated tests: tampered price ignored, success URL without payment grants nothing, duplicate webhook processed once, out-of-order events end in correct state, entitlement checks per plan.
- StoreKit testing in Xcode (StoreKit configuration file), Play license testers.

## 12. Reconciliation and monitoring

- Daily job: list active subscriptions at the provider ↔ your `subscriptions` + `entitlements`; payments ↔ `payments`; alert on mismatches.
- Monitor webhook failures (provider dashboard + your logs), dispute rate, failed payment rate, MRR/churn (provider analytics or ChartMogul/Baremetrics).

## 13. Launch checklist

- [ ] Live keys only on server, restricted keys where possible; webhook secret for live endpoint.
- [ ] Business details, statement descriptor, support email, refund policy, terms and privacy linked at checkout.
- [ ] Tax registration/collection configured for target markets.
- [ ] Customer portal configured (cancel, update card, invoices).
- [ ] Emails: receipt, trial ending, payment failed, canceled, refund.
- [ ] Reconciliation job and alerts on.
- [ ] Small real transaction tested end to end, then refunded.

## 14. Pricing page

`design-system/references/patterns.md` §2: 2–4 plans, highlight one, annual savings, feature comparison, FAQs on cancel/refund/data, local currency, VAT clarity.
