---
name: legal-compliance
description: Load before launch, when collecting personal data, adding analytics/cookies, building sign-up or account deletion. Privacy policy, terms, consent, user rights, retention, GDPR, Saudi/UAE PDPL, store privacy. Triggers: privacy policy, GDPR, سياسة الخصوصية, الكوكيز.
---

# Legal and Compliance (product side)

This skill makes the product capable of complying: the pages, flows, records and controls the law and the app stores expect. It is not legal advice; for regulated sectors (health, finance, children, government), high volumes of sensitive data, or disputes, involve a qualified lawyer in each country you operate in.

| File | Use it for |
|------|-----------|
| `references/privacy-and-terms.md` | Data inventory template, privacy policy and terms outlines, cookie/consent rules and implementation, user-rights flows, account deletion, retention schedule, processors/DPAs, transfers, children, marketing, AI disclosures, accessibility statement, regional law summary, store requirements, launch checklist |
| `scripts/legal_check.py` | Check for privacy/terms pages, account deletion and data export when auth exists, consent handling when analytics/ads load, Google Fonts/YouTube embeds that leak IPs before consent |

## 1. Rules

1. **Know your data**: a data inventory (what, why, where stored, who receives it, how long) before writing the privacy policy. The policy describes reality, not a template.
2. **Collect the minimum** for the stated purposes; no "might be useful later" fields; sensitive data (health, biometrics, children, precise location, religion) only with a strong reason and extra protection.
3. **Privacy policy and terms** are linked from the footer, sign-up, checkout and app store listings, in every language the product supports (Arabic and English), dated and versioned.
4. **Consent where required, before the tracking happens**: non-essential cookies/SDKs (analytics, ads, session replay) load only after opt-in in GDPR-style regimes; reject is as easy as accept; choices stored and revocable.
5. **User rights are features**: access/export, correction, deletion (in-app account deletion, required by both app stores for apps with account creation), objection/opt-out of marketing and of sale/sharing where applicable. Respond within legal deadlines.
6. **Retention is defined and enforced** by jobs, not by intention.
7. **Processors are listed and contracted** (DPAs with hosting, email, analytics, AI providers); cross-border transfers have a legal mechanism.
8. **Record consent and acceptance**: who accepted which version of terms/privacy, when; marketing consent separately from terms.
9. **Breach readiness**: incident process with notification timelines (e.g. 72 hours to the regulator under GDPR; check local law) (`launch-security` incident card).
10. **Store compliance**: privacy labels/Data safety forms match actual SDK behavior; privacy policy URL; account deletion; ATT on iOS for tracking (`launch-security` S3–S5, `mobile-release`).

## 2. Workflow

1. Fill the data inventory (`privacy-and-terms.md` §1) from code (`launch-security` SECURITY_MAP.md helps), SDKs and providers.
2. Decide jurisdictions (where users are, where the company is) → applicable laws (§11).
3. Write privacy policy, terms, cookie policy from the outlines (§2–§4); have them reviewed when stakes are high.
4. Implement: consent banner/manager (if needed), account deletion, data export, marketing preferences, retention jobs, consent records.
5. Run `python3 <skill>/scripts/legal_check.py .` → 0 ERROR; check stores' privacy forms.
6. Launch checklist (§13).

## 3. Done when

- [ ] Data inventory exists and matches code/SDKs; privacy policy reflects it; terms published; both bilingual where the product is.
- [ ] Consent manager blocks non-essential trackers until opt-in where required; choices persist and can be changed.
- [ ] In-app account deletion and data export work end to end (including third-party processors).
- [ ] Retention jobs run; processors listed with DPAs; transfer mechanisms in place.
- [ ] Acceptance and marketing-consent records stored with versions.
- [ ] `legal_check.py` 0 ERROR; store privacy forms accurate.
