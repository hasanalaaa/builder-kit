# Bonus checks B1–B7 and incident response

Apply SKILL.md §1 "Rules of work" and the "Finish every check with" table to every check here.

---

## B1 · Secure AI features · HIGH

Risk: prompt injection ("ignore your instructions…") via user text, uploaded documents, emails or web pages; system-prompt extraction; unauthorized tool actions; cost abuse.

1. List each LLM call: model, where the API key lives (must be server-only), what user content and which documents/data go into the prompt, what the output is used for.
2. Prompt injection: assume any user text/file/email/page fed to the model contains hostile instructions. The model must not be able to reveal secrets (no keys or other users' data in prompts), access data the current user can't see, or trigger tools/actions beyond that user's permissions. Destructive or costly actions need explicit user confirmation.
3. Output is untrusted: sanitize before rendering as HTML/Markdown (check 07); validate before using in queries, URLs, code or commands.
4. Cost: auth required, per-user rate limits and daily quotas, max input and output tokens, provider-side monthly spending cap.
5. Privacy: send the model only the personal data it needs; log prompts carefully or not at all.

Fix the issues and list what changed.

---

## B2 · Block SSRF in URL-fetching features · HIGH

Risk: features that fetch a user-supplied URL (link previews, import-from-URL, outgoing webhooks, image-from-URL, PDF/screenshot generation, browsing AI tools) can be pointed at internal networks or the cloud metadata service.

For each such feature:
- Allow only `http`/`https`.
- Resolve the hostname and block private, loopback, link-local and internal ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16` (incl. metadata IP `169.254.169.254`), `::1`, `fc00::/7`. Check the initial request AND every redirect.
- Domain allowlist where possible.
- Short timeouts and a max response size.
- Never return raw internal error details.
- Use a maintained SSRF-protection library if one fits the stack.
- Add tests using internal addresses.

---

## B3 · Backups you can actually restore · HIGH

1. What's backed up (DB, file storage, config), how often, where stored, retention. Is point-in-time recovery available on the DB plan?
2. Are backups protected from production credentials (so an attacker or mistake can't delete both)?
3. Write `RESTORE.md`: step-by-step restore of DB and files into a new environment, and how to run a test restore without touching production.
4. Recommend the minimum setup for the stack/plan with exact dashboard steps.

Backups only count once a restore has been tested.

---

## B4 · Lock down the owner's accounts · CRITICAL

One phished password on GitHub, hosting, registrar, DB dashboard, Stripe or email bypasses every other check.

From the codebase/config, list every service depended on (code hosting, hosting/deploy, DNS and registrar, DB, auth provider, payments, email, AI providers, analytics, error tracking, app stores). For each, a tickable checklist:
- [ ] MFA on (authenticator app or passkey, not SMS where possible)
- [ ] Team members reviewed; remove anyone who no longer needs access
- [ ] Least-privilege roles
- [ ] Connected OAuth apps and integrations reviewed
- [ ] Active API keys and deploy tokens reviewed
- [ ] Login/security alerts on
- [ ] Domain lock on at the registrar

---

## B5 · Spending caps and abuse alarms · HIGH

Likely "attack" for AI-built apps: a surprise bill (leaked AI key, loop hitting a paid API, SMS pumping, traffic spike on usage-based hosting).

List every usage-billed service (hosting, serverless, DB, storage, bandwidth, AI/LLM, email, SMS, maps, search). For each, exact steps to set: (1) a billing alert, (2) a hard spending cap/quota if supported, (3) per-key usage limits. SMS: restrict destination countries. Add app-level per-user quotas on the most expensive features and a simple daily usage summary in the logs.

---

## B6 · Privacy and data minimisation · MEDIUM

Data you don't collect can't leak. GDPR (EU), India's DPDP Act, CCPA (California) and others may require view/export/delete rights and breach notification.

Map every piece of personal data: where stored, who can see it, which third parties receive it (analytics, AI providers, email, error tracking), retention. Then:
- Flag data not actually needed.
- Stop unnecessary personal data going to analytics/error tracking.
- Implement (or plan) account deletion that removes/anonymizes the user's data across DB, storage and third parties.
- Implement a user data export.
- List what the privacy policy must mention based on what the app really does. Mark items needing legal review.

---

## B7 · Protect the email domain · MEDIUM

Without SPF, DKIM and DMARC anyone can send mail that looks like it's from the domain (perfect for fake "reset your password" phishing); they also keep real mail out of spam.

From the email provider(s) used (transactional and personal), give exact DNS records:
- SPF: ONE record listing all senders.
- DKIM: from each provider.
- DMARC: start `p=none` with a reporting address; move to `quarantine`/`reject` once reports are clean.

Also check app emails carry no unnecessary sensitive data and links use the configured `APP_URL`. Give steps to verify with a free checker.

---

## Incident response (something went wrong)

Triggers: a leaked key, strange charges, users reporting account activity they didn't do, data changing on its own.

When the user reports a suspected compromise, help in this order:
1. **Containment:** the first three actions for the next 15 minutes, exact steps.
2. **Credentials to rotate first** and how, without unnecessary downtime (check 25 order: payments, cloud, DB first).
3. **Where to look:** code, logs and provider dashboards, with exact queries/filters.
4. **Most likely vulnerability** given the codebase, with the fix plus a test.
5. **A plain-language summary** the user can adapt to tell affected users.

Never print secret values. Ask before running anything destructive.

**Leaked an API key right now?** Revoke it immediately in the provider dashboard, even before a replacement is deployed, if it's a payment, cloud or AI key. A few minutes of downtime is cheaper. Then follow check 25.

**The incident card, in order:**
0. Stay calm, keep evidence: don't delete logs, users or the repo. Write down what was noticed and when.
1. Stop the bleeding: rotate exposed keys (payments, cloud, DB first). Maintenance mode for the affected feature if needed.
2. Kill sessions: rotate session/JWT secrets or revoke sessions; force password resets if accounts were affected.
3. Investigate: app logs, DB logs, provider dashboards: when it started, what was accessed, which accounts.
4. Close the hole: fix the vulnerability, add a test proving it (check 27), deploy.
5. Check the data: read/changed/deleted? Backups intact (B3)?
6. Tell people: if personal data was affected, tell users honestly. Laws like GDPR (72-hour regulator notice) or India's DPDP Act may require formal notification. Recommend legal advice.
7. Learn: short post-mortem: cause, impact, fix, what prevents a repeat.
