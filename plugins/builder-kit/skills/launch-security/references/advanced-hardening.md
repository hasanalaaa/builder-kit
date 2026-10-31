# Advanced hardening: checks H1–H16 (beyond the 27)

Apply SKILL.md §1 "Rules of work" and the "Finish every check with" table. The 27 checks are the baseline. These close the gaps that the current industry standards cover:

- **OWASP Top 10:2025:** A01 Broken Access Control · A02 Security Misconfiguration · A03 Software Supply Chain Failures · A04 Cryptographic Failures · A05 Injection · A06 Insecure Design · A07 Authentication Failures · A08 Software or Data Integrity Failures · A09 Logging & Alerting Failures · A10 Mishandling of Exceptional Conditions.
- **OWASP ASVS 5.0** (May 2025, 17 chapters): the verification target. Default **Level 2** for any app with user accounts; **Level 3** for payments at scale, health, finance or children's data.
- **OWASP API Security Top 10 (2023):** BOLA, broken authentication, BOPLA (property-level), unrestricted resource consumption, BFLA (function-level), sensitive business flows, SSRF, misconfiguration, improper inventory, unsafe API consumption.
- **OWASP Top 10 for LLM applications + Agentic AI Top 10:** see platforms.md P4.

Verify any version-specific fact against the official OWASP pages before quoting it in a report.

---

## H1 · Threat model every feature (A06 Insecure Design) · HIGH

Before building a feature that touches money, identity, user data, files, AI, or admin power, write 5–10 lines in `SECURITY_MAP.md` → "Threat notes":
- Assets (what's valuable), actors (anonymous, user, other tenant, admin, insider, bot), entry points.
- STRIDE prompts: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege. One line each: how, and the control that stops it.
- Abuse cases: "How would I cheat this feature for free value?" (trials, referrals, coupons, credits, invites, voting, rate-limited actions).
- Trust boundaries: what the client controls vs what the server decides.

**Done when:** each sensitive feature has threat notes, and every listed threat maps to a control or a test.

---

## H2 · Authorization at every layer (A01, API1/API3/API5) · CRITICAL

Extends 01/03/09.
- **Object level (BOLA/IDOR):** every object access checks ownership/tenant, including nested routes (`/teams/:t/projects/:p`: check that `p` belongs to `t` AND the user belongs to `t`).
- **Property level (BOPLA):** response serializers allowlist fields per role; write schemas allowlist fields per role (mass assignment, 06).
- **Function level (BFLA):** every privileged operation checks role; HTTP method changes (GET→DELETE) don't bypass it.
- **Multi-tenancy:** tenant ID comes from the session, never the request; every query is tenant-scoped (Postgres RLS on `tenant_id` is the strongest option); caches, search indexes, file paths and background jobs are tenant-scoped too.
- Centralize policy in one module (e.g. `can(user, action, resource)`) and deny by default.
- IDs: prefer non-sequential IDs (UUIDv4/v7) for public references. This hides volume; it is NOT a substitute for authorization.

**Verify:** an automated authorization matrix test: roles × endpoints × own/other-tenant resources → expected status.

---

## H3 · Strong authentication (A07, ASVS V6) · HIGH

Extends 01/05/15/17.
- Offer **passkeys (WebAuthn)** or TOTP MFA; require MFA for admins and for high-value accounts. SMS OTP only as fallback.
- Credential stuffing defence: rate limits (12) + breached-password check + optional bot challenge (Turnstile/hCaptcha) after failures. Never lock accounts permanently by username (it's a DoS); use progressive delays.
- New-device / new-location login notification; list of active sessions with "revoke".
- OAuth/OIDC (ASVS V10): Authorization Code + **PKCE**; validate `state`, `nonce`, `iss`, `aud`, `exp`; exact redirect URIs; never the implicit flow; never put tokens in URLs.
- Tokens (ASVS V9): short-lived access tokens, rotating refresh tokens with reuse detection, an allowlist of algorithms, key rotation via `kid` + JWKS.
- Email change: confirm with the OLD address too, then notify it.

---

## H4 · Cryptography and data protection (A04, ASVS V11/V12/V14) · HIGH

- Never invent crypto. Use the platform/libsodium/Web Crypto: AES-256-GCM or ChaCha20-Poly1305 for encryption, Argon2id/bcrypt for passwords, HMAC-SHA-256 for signatures, CSPRNG for all tokens.
- TLS 1.2+ only (prefer 1.3); no TLS 1.0/1.1; HSTS (04).
- Encryption at rest for databases, backups and object storage (usually a toggle at the provider). Field-level encryption for highly sensitive fields (national IDs, health data, tokens for third-party accounts), with keys in a KMS/secrets manager, not in the DB.
- Constant-time comparison for secrets and signatures.
- Data classification: tag each field public / internal / personal / sensitive. Sensitive data never in URLs, logs, analytics, error trackers or client caches.
- Retention: delete data you no longer need on a schedule (B6).

---

## H5 · Fail safely (A10 Mishandling of Exceptional Conditions) · HIGH

- **Fail closed:** when an auth check, permission lookup, payment verification, signature check or external call errors or times out, deny. Never `catch { return true }` or "allow if the service is down".
- Every external call has a timeout, bounded retries with backoff, and a circuit breaker for critical dependencies.
- Transactions: multi-step writes (charge + fulfil, debit + credit) are atomic or have compensating actions; no half-finished state left on error.
- No empty catch blocks; unexpected errors are logged with request ID (08) and return a generic message (20).
- Resource exhaustion handled: queue backpressure, memory limits, and disk-full behave predictably.

**Verify:** tests that force dependency failures (auth provider down, DB timeout, payment API 500) and assert access is denied and state is consistent.

---

## H6 · Abuse-resistant business logic (API6) · HIGH

- Race conditions: use DB constraints (unique indexes), row locks (`SELECT … FOR UPDATE`) or atomic updates (`UPDATE … SET credits = credits - 1 WHERE credits > 0`) for balances, coupons, stock, votes, invites and one-time actions. Test with parallel requests.
- Idempotency keys on create/charge endpoints so retries don't duplicate.
- State machines: enforce allowed transitions on the server (an order can't go from `cancelled` to `shipped`; steps can't be skipped).
- Limits on every free resource: trials per device/payment method/phone, referrals, invites, storage, AI tokens.
- Sensitive flows (sign-up, checkout, posting) protected from automation with rate limits, bot detection, and anomaly alerts.

---

## H7 · Resource consumption and DoS (API4) · HIGH

- Every list endpoint is paginated with a **max page size**; no unbounded queries or exports.
- Request body size, upload size, JSON depth and array length limits.
- Timeouts on requests, DB queries (`statement_timeout`) and background jobs.
- Regex: avoid catastrophic backtracking (ReDoS) on user input; use linear-time engines (RE2) or bounded patterns.
- GraphQL: query depth and complexity limits, persisted queries or allowlists in production, introspection off (20), batching limits.
- Expensive operations (AI, image processing, PDF, email) run in queues with per-user concurrency caps.
- CDN/WAF in front (Cloudflare, Vercel WAF, AWS WAF) with bot protection and DDoS mitigation for public apps.

---

## H8 · More injection and parsing risks (A05, A08) · HIGH

Extends 07/10.
- **Insecure deserialization:** never `pickle`, Java native serialization, PHP `unserialize`, or YAML `load` (use `safe_load`) on untrusted data.
- **XXE:** disable external entities/DTDs in XML parsers.
- **Path traversal:** never build file paths from input; resolve and verify the path stays inside the base directory.
- **Prototype pollution (JS):** don't deep-merge untrusted objects into plain objects; block `__proto__`, `constructor`, `prototype` keys; validate with strict schemas.
- **Template injection (SSTI):** never compile user input as a template.
- **Header/CRLF and email header injection:** strip `\r\n` from values placed in headers or email fields.
- **Open redirects:** every redirect target allowlisted (01).
- **CSV/formula injection** (18) and **log injection** (08).
- **Client-side:** `postMessage` handlers check `event.origin`; no `target="_blank"` without `rel="noopener"`; Subresource Integrity (`integrity=`) on third-party scripts from CDNs; Trusted Types where supported.

---

## H9 · Caching and HTTP edge cases (A02) · MEDIUM

- Personalized responses: `Cache-Control: private, no-store`; CDN never caches authenticated pages (watch for web cache deception: `/account/profile.css` served from cache).
- `Vary` headers correct when responses differ by cookie/auth/origin.
- Host header validated (17) and not used to build URLs.
- Reverse proxy and app agree on request parsing (avoid request smuggling: keep proxies updated, reject ambiguous `Content-Length`/`Transfer-Encoding`).
- WebSockets: authenticate on connect AND authorize every message/channel subscription; check `Origin`; rate-limit messages.
- `security.txt` at `/.well-known/security.txt` with a contact and a disclosure policy.

---

## H10 · Software supply chain and CI/CD integrity (A03, A08) · HIGH

Extends 21/22/24.
- Lockfile committed; install with frozen lockfile; consider `npm ci --ignore-scripts` (or pnpm's default of not running dependency build scripts) and allowlist the packages that need scripts.
- Pin GitHub Actions to a **full commit SHA**, not a tag; least-privilege `permissions:` block (`contents: read` by default); never run untrusted PR code with secrets (`pull_request_target` hazards).
- Use OIDC federation from CI to the cloud instead of long-lived cloud keys.
- Branch protection: required reviews and required status checks on the main branch; signed commits/tags for releases if the team can support it.
- Generate an **SBOM** (CycloneDX/SPDX) for releases; aim for SLSA build provenance where the platform supports it.
- Third-party scripts in the browser (analytics, chat, tag managers) are supply chain too: minimize, SRI where possible, CSP allowlist (14).
- Watch for dependency confusion: scope private packages, set the registry per scope.

---

## H11 · Infrastructure, cloud and containers (A02) · HIGH

- Cloud IAM least privilege; no wildcard (`*`) actions on production; root/owner account with hardware-key MFA and no access keys (B4).
- Storage buckets private by default; block public access at the account level.
- Databases, caches and admin panels on private networks; no public ports except 443 (and 80 for redirect). SSH by key only, or no SSH (use the provider's session manager).
- Containers: minimal base images, non-root user, read-only filesystem where possible, no secrets in images or build args, image scanning (e.g. Trivy/Grype).
- Infrastructure as Code scanned (e.g. Checkov/tfsec); no drift from manual console changes.
- Separate accounts/projects for dev, staging and production; production data never copied to dev without anonymization.
- Preview/staging deployments protected by auth (20).

---

## H12 · Secrets management at scale · MEDIUM

Extends 02/11/25.
- Secrets in the host's encrypted env store or a secrets manager (Vault, AWS/GCP Secrets Manager, Doppler, 1Password, Infisical), never in repo, chat, tickets or docs.
- Separate keys per environment and per service; scope each key to minimum permissions.
- A rotation schedule for high-value keys (quarterly) and automatic rotation where the provider supports it.
- Short-lived credentials (OIDC, STS) over static keys wherever possible.

---

## H13 · Automated security pipeline in CI · HIGH

Every push / PR runs (use current, maintained tools; verify names and versions before adding):
- **Secrets scan:** gitleaks or TruffleHog (24).
- **SCA / dependency audit:** `npm audit` / `pip-audit` / OSV-Scanner + Dependabot or Renovate (21).
- **SAST:** Semgrep and/or GitHub CodeQL with security rules for the stack.
- **Security tests** from check 27.
- **IaC / container scan** if applicable (H11).
- **DAST baseline** against staging on deploy (e.g. OWASP ZAP baseline scan), plus `scripts/check-headers.sh` and `scripts/check-exposed.sh`.
High/Critical findings fail the build; exceptions are documented with an owner and expiry date.

---

## H14 · Detection and response maturity (A09) · MEDIUM

Extends 08 and the incident card.
- Audit log for sensitive actions is append-only (separate table/service, no update/delete permissions for the app).
- Alerts routed to a human channel (email/Slack/phone), tested at least once.
- Anomaly signals: impossible travel, sudden spikes in exports/downloads, many 403s from one user (IDOR probing), webhook signature failures, admin logins from new devices.
- Uptime and certificate-expiry monitoring.
- An incident contact list and the incident card (bonus-and-incident.md) kept in the repo.

---

## H15 · Privacy engineering and compliance · MEDIUM

Extends B6.
- Consent: analytics/marketing cookies and trackers only after consent where the law requires it (EU/UK GDPR + ePrivacy, and others); honour Global Privacy Control where required.
- Data subject requests: export and deletion work end to end (S3).
- Records of processors (every third party that receives personal data) and their data-processing agreements.
- Data residency requirements for the user's market (e.g. Saudi PDPL, EU GDPR, India DPDP): know where data is stored and whether cross-border transfer is allowed.
- Children: if under-13/16 users are possible, follow COPPA / GDPR-K rules or block them.
- Mark items needing legal review; this skill doesn't replace a lawyer.

---

## H16 · Independent assurance · REVIEW

- Before launch for anything handling payments, health, finance, children's data or large user bases: an external penetration test or professional review, scoped to ASVS Level 2/3.
- After launch: a vulnerability disclosure policy (`security.txt`), and a bug bounty when the app is mature.
- Re-test after every major feature (26 + 27).
