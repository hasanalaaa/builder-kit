# Privacy, terms and compliance reference

Not legal advice. Laws change; verify current requirements for your countries and sector.

## 1. Data inventory (keep as `docs/data-inventory.md`)

| Data | Source | Purpose | Lawful basis / consent | Stored where (region) | Shared with (processors) | Retention | Sensitive? |
|------|--------|---------|------------------------|-----------------------|--------------------------|-----------|-----------|
| Email | sign-up | account, login, service emails | contract | Supabase (eu-central) | Resend | account life + 30 days | no |
| IP address | every request | security, rate limiting | legitimate interest | logs (Axiom) | — | 30 days | no |
| Analytics events | client | product improvement | consent (EU) | PostHog (EU) | PostHog | 12 months | no |
| Child photos | staff upload | service | contract + parental consent | private storage | — | 12 months | yes |

Include SDKs in mobile apps (analytics, crash, ads, attribution) — they collect data too.

## 2. Privacy policy outline

1. Who we are (legal entity, address, contact, DPO/representative if required).
2. What we collect (by category: account, content, usage, device, payment via processor, communications) and from where.
3. Why we use it (purposes) and the legal basis per purpose (GDPR-style) or notice per law.
4. Cookies and similar technologies (link to cookie policy / settings).
5. Who we share with (processors by category, named where required; no selling, or opt-out if "sale/share" under CCPA).
6. International transfers and safeguards.
7. Retention periods.
8. Your rights and how to exercise them (in-app links, email), response time, right to complain to the regulator.
9. Security measures (high level).
10. Children (minimum age; parental consent process if applicable).
11. AI features (what data is sent to AI providers, whether used for training — usually not —, retention).
12. Changes to this policy (versioning, notification).
13. Contact.
Write plainly; short summary at the top; Arabic version written natively (not machine-only).

## 3. Terms of service outline

Parties and acceptance · eligibility and accounts · the service and changes · acceptable use (prohibited content/conduct) · user content license and responsibilities · paid plans, billing, renewals, cancellation, refunds (matching `payments-billing`) · intellectual property · third-party services · disclaimers and limitation of liability (within local law) · indemnity (B2B) · termination and suspension · governing law and disputes · changes to terms · contact. For marketplaces/UGC: content moderation, reporting, takedown process. For B2B: separate DPA and possibly SLA.

## 4. Cookies and consent

- Strictly necessary (session, security, load balancing, consent choice): no consent needed; explain them.
- Preferences, analytics, marketing/ads, session replay: consent required in EU/UK (ePrivacy) and several other jurisdictions before setting/reading identifiers.
- Banner: accept all / reject all with equal prominence, settings for categories, no pre-ticked boxes, no "by continuing you agree", link to policy, re-ask after 6–12 months or when purposes change.
- Implement: consent manager (Cookiebot, OneTrust, Usercentrics, Klaro, CookieYes, or a small custom one) + Google Consent Mode v2 if using Google tags; load scripts conditionally; record consent (timestamp, version, choices).
- Alternatives: cookieless analytics (Plausible, Umami, Fathom, PostHog cookieless mode) may avoid consent for analytics in many cases; verify per jurisdiction.
- Self-host fonts and use privacy-enhanced embeds (youtube-nocookie, click-to-load maps/videos) so third parties don't receive IPs before consent.

## 5. User rights flows

| Right | Product feature |
|-------|-----------------|
| Access / portability | "Download my data" → background job builds JSON/CSV zip → emailed link (expiring, authenticated) |
| Deletion | In-app "Delete account" (settings), re-auth, clear consequences, optional grace period (e.g. 30 days) then hard delete/anonymize across DB, storage, search index, analytics (delete person), email provider, payment provider customer (keep invoices as legally required), backups age out |
| Correction | Editable profile; support path for other data |
| Objection / opt-out | Marketing unsubscribe; analytics opt-out; "Do not sell or share" link (CCPA) if applicable; Global Privacy Control signal honored where required |
| Restriction | Support process |
Verify identity before fulfilling requests; log requests and responses; deadlines (GDPR: 1 month; CCPA: 45 days; check local law).

## 6. Retention schedule

Define per data type; implement with scheduled jobs (`data-design` §6): deleted accounts purged after grace period, logs 30–90 days, inactive accounts notified then deleted after N years (if policy says so), backups expire on rotation, invoices kept per tax law (often 5–10 years).

## 7. Processors and transfers

- List processors (hosting, DB, email, analytics, error tracking, AI, payments, support tools) with purpose and region; sign DPAs (most providers have click-through DPAs).
- Prefer data regions close to users or required by law (some Gulf rules prefer or require in-country storage for certain sectors/data).
- Transfers out of the EU/UK: adequacy decisions, EU-US Data Privacy Framework (for certified US providers), or Standard Contractual Clauses. Other countries have their own transfer rules (e.g. Saudi PDPL transfer regulations).

## 8. Children

- US COPPA: verifiable parental consent for under-13 data collection; GDPR: age of digital consent 13–16 by country; app stores' Kids categories add strict rules (no third-party analytics/ads without exceptions, parental gates).
- If not for children: state minimum age, age gate at sign-up where appropriate.
- If for children or schools: data minimization, parental controls, no behavioral ads, specialized review.

## 9. Marketing

- Consent for marketing emails/SMS/WhatsApp where required (opt-in checkbox, unticked, separate from terms); soft opt-in for existing customers only where the law allows.
- Unsubscribe in every message, one-click for email (`email-notifications`); honor quickly.
- Keep consent records; sender identification; no purchased lists.

## 10. AI transparency

- Tell users when they interact with AI (chatbots) and when content is AI-generated where required (EU AI Act transparency obligations phase in from 2026; some platforms require labels).
- Explain what data goes to AI providers, opt-outs, and that it isn't used for training (if true, per provider settings).
- High-risk uses (hiring, credit, education scoring, biometric) have heavy obligations: get legal advice.

## 11. Regional summary (verify current details)

| Jurisdiction | Law | Highlights |
|--------------|-----|-----------|
| EU / EEA | GDPR + ePrivacy | Lawful basis, consent for non-essential cookies, rights within 1 month, DPO in some cases, 72h breach notice, fines up to 4% turnover |
| UK | UK GDPR + PECR | Similar to GDPR |
| California / US states | CCPA/CPRA and other state laws | Notice at collection, opt-out of sale/sharing (incl. targeted ads), GPC signal, sensitive data limits; many states now have comprehensive privacy laws |
| Saudi Arabia | PDPL (enforced since Sept 2024) + implementing and transfer regulations; SDAIA as regulator | Consent and lawful bases, data subject rights, transfer restrictions, breach notification, registration requirements for some controllers |
| UAE | Federal PDPL (Decree-Law 45/2021); DIFC and ADGM have their own data protection laws | Rights, transfers, breach notification; free zones differ |
| Qatar, Bahrain, Oman, Kuwait | National data protection laws/regulations | Consent, rights, transfers; sector rules (banking, health, telecom) |
| Egypt | PDPL 151/2020 | Licensing/registration obligations, consent, transfers |
| Sector rules | Health (HIPAA in US, local health data rules), payments (PCI DSS), finance (central bank rules) | Usually stricter than general law |

## 12. Accessibility statement and other pages

- Accessibility statement: standard targeted (WCAG 2.2 AA), known limitations, contact for barriers, date (`accessibility`).
- Imprint/company details where required (e.g. Germany), refund/returns policy (e-commerce), shipping policy, community guidelines (UGC), security.txt (`/.well-known/security.txt`) for vulnerability reports.

## 13. Launch checklist

- [ ] Data inventory complete; privacy policy and terms published (ar + en), linked in footer, sign-up, checkout, stores.
- [ ] Consent manager live where needed; trackers blocked before consent; Google Consent Mode configured if applicable.
- [ ] Account deletion and data export tested end to end.
- [ ] Marketing consent separate; unsubscribe works.
- [ ] Processors' DPAs signed; regions documented; transfer mechanisms.
- [ ] Retention jobs scheduled; backups retention known.
- [ ] Store privacy labels / Data safety form accurate; ATT prompt if tracking.
- [ ] Acceptance records (terms version, timestamp) stored.
- [ ] Incident/breach process documented with contacts and notification timelines.
