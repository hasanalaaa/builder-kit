# Data & Inputs: checks 03, 06, 07, 10, 18, 19

Apply SKILL.md §1 "Rules of work" and the "Finish every check with" table to every check here.

---

## 03 · Secure the database · CRITICAL

Goal: users read and change only their own data, even when talking to the database directly.

**Self-check:** two test accounts; as A, replay a request with B's ID → 403/404. Supabase: Table Editor shows RLS on every table; run Advisors → Security Advisor and fix every warning. Firebase: rules contain no `allow read, write: if true` or date-based test-mode rule.

**Audit**
1. Every table/collection and storage bucket: who may read/create/update/delete (owner, team, admin, public).
2. How the app reaches the DB: server only, or directly from browser (Supabase client, Firebase SDK…).
3. Browser talks to DB directly:
   - Supabase/Postgres: RLS ENABLED on every table in exposed schemas; separate SELECT/INSERT/UPDATE/DELETE policies on `auth.uid()`; INSERT/UPDATE have `WITH CHECK` (can't create rows for others or change `owner_id`/`user_id`). Views bypass RLS unless `security_invoker = true`. `SECURITY DEFINER` functions bypass RLS and must check permissions themselves. Never base policies on `user_metadata`.
   - Firebase: per-path rules on `request.auth.uid`, validating written fields; no test-mode / `if true`.
   - Storage buckets: private by default; users access only their own files.
4. Access via server: every fetch/update/delete by ID also checks ownership/permission. List endpoints where a client ID reaches an unscoped query (IDOR).
5. service_role/admin key and DB connection string used ONLY in server code.
6. DB user not superuser; DB not open to the internet (IP allowlist, no `0.0.0.0/0`); TLS connections; automated backups on.
7. API responses never return sensitive columns (hashes, tokens, other users' emails, internal flags). Select only needed fields.

**Fix:** write missing policies/rules and ownership checks. Show every policy in full SQL/rules syntax with a one-line plain-language explanation.

**Verify:** test/script with two test users proving A cannot read/update/delete B's rows or files, and a signed-out visitor with only the public key gets nothing private.

**Watch out:** RLS on with no policies blocks everything; RLS off allows everything. Views and SECURITY DEFINER functions are the classic RLS bypass. MongoDB Atlas `0.0.0.0/0` + weak password is a common breach.

**Done when**
- [ ] RLS/security rules enabled on every table, collection and bucket.
- [ ] User A cannot read, edit or delete user B's data (tested, not assumed).
- [ ] Admin/service keys only in server code.
- [ ] DB not open to the whole internet; backups on.
- [ ] API responses never include password hashes or other users' private fields.

---

## 06 · Server-side validation · HIGH

Goal: browser validation is UX; server validation is security. Accept only expected fields.

**Self-check:** DevTools → copy a form request as fetch, edit values (negative numbers, 100,000-char strings, wrong types), send. Add `"role":"admin"` or `"credits":99999` to a profile update → must be ignored/rejected.

**Audit**
1. Table of every endpoint, server action, form handler, webhook and background job accepting outside input (body, query, URL params, headers, cookies, upload metadata) and its fields.
2. Is each validated on the server today, and how?
3. Mass assignment: request body (or a spread like `{...req.body}` / `**data`) passed straight into DB create/update. Flag server-controlled fields: `id`, `user_id`/`owner_id`, `role`, `is_admin`, `price`, `amount`, `status`, `credits`, `balance`, `plan`, `is_verified`, `email_verified`, `created_at`.

**Fix**
- ONE validation library for the stack (Zod for TS, Pydantic for Python…), validated at the very start of each handler, before business logic or DB calls.
- Per field: type, required/optional, number min/max, max length for EVERY string, enums, formats (email, URL, UUID, date), money as integer minor units.
- Reject unknown fields (strict); copy only allowed fields into writes. Server-owned fields never from client.
- Normalize (trim, lowercase emails) before saving.
- Consistent 400 with field-level messages; never a stack trace.
- Max request body size.
- Share schemas with the front end where possible; the server check is the one that counts.

**Verify:** tests sending a negative quantity, a 100,000-char string, a wrong type, a missing required field, an extra `"role":"admin"` → each rejected or ignored; nothing invalid reaches the DB.

**Watch out:** TypeScript types don't exist at runtime. Valid text can still carry HTML (check 07).

**Done when**
- [ ] Every input-accepting endpoint validates on the server with a schema.
- [ ] Every string has a max length; every number a range.
- [ ] Unknown fields rejected; server-owned fields can't be set by clients.
- [ ] Invalid input returns a clean 400, never a crash or stack trace.

---

## 07 · Protect against XSS · HIGH

Goal: user text is always shown as text, never run as code.

**Self-check:** enter `<img src=x onerror=alert(1)>` in every displayed field (name, bio, comment, title) → no alert anywhere. Put `javascript:alert(1)` in URL fields and click. Search code for `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, `{@html`.

**Audit**
1. Dangerous sinks with file:line and data source:
   - React `dangerouslySetInnerHTML`; Vue `v-html`; Svelte `{@html}`; Angular `[innerHTML]`, `bypassSecurityTrust*`.
   - DOM: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, jQuery `.html()`/`.append()` with strings.
   - Server templates: `|safe`, `mark_safe`, autoescape off, `Markup()`, EJS `<%- %>`, Handlebars `{{{ }}}`, `raw()` helpers.
   - Code execution: `eval`, `new Function`, `setTimeout`/`setInterval` with strings.
2. User URLs in `href`/`src`/`action`/`window.location`: only `http:`, `https:`, `mailto:`; block `javascript:` and `data:`.
3. User data inside `<script>` tags, inline event handlers, style attributes, or JSON embedded in HTML.
4. Markdown/rich text (raw HTML allowed?), rich-text editors, SVG uploads, HTML emails/PDFs with user content.
5. AI/LLM output is untrusted input; sanitize if rendered as HTML/Markdown.

**Fix**
- Prefer framework escaped rendering (`{value}` in JSX, `{{ }}` in templates).
- Where HTML is genuinely needed: DOMPurify (browser) or a maintained server sanitizer with strict tag/attribute allowlist.
- Validate URL schemes before rendering links.
- Session cookies HttpOnly (check 15); prepare CSP (check 14) as second line of defence.

**Verify:** tests submitting `<img src=x onerror=alert(1)>`, `"><svg onload=alert(1)>`, `javascript:alert(1)` through each affected input, asserting harmless text.

**Watch out:** admin panels are a favourite target (stored XSS firing for an admin). Sanitize on output, not only input.

**Done when**
- [ ] No unsanitized `innerHTML`/`dangerouslySetInnerHTML`/`v-html` with user data.
- [ ] User links allow only http, https, mailto.
- [ ] Markdown/rich text and AI output are sanitized.
- [ ] XSS payloads render as plain text everywhere.

---

## 10 · Parameterized queries · CRITICAL

Goal: query structure is fixed; user input is only data. Covers SQL, NoSQL, filter-string and command injection.

**Self-check:** search for SQL built with template strings or `+` (`` `SELECT … ${ ``, `f"SELECT … {`, `"… WHERE id = " +`). Search ORM escape hatches: `$queryRawUnsafe`, `$executeRawUnsafe`, `sequelize.literal`, `knex.raw(`, `.extra(`, `text(f"…")`. Type `'` into search boxes; a 500/SQL error is a red flag.

**Audit**
1. Every query whose text is built from variables via concatenation, template literals, f-strings, `.format()` or `%`.
2. ORM escape hatches with untrusted input: Prisma `$queryRawUnsafe`/`$executeRawUnsafe`/`Prisma.raw` (tagged `` $queryRaw`...${value}` `` IS safe), Sequelize `literal()`/raw, Knex `raw()` with interpolation, TypeORM `query()` with strings, SQLAlchemy `text()` with f-strings, Django `raw()`/`extra()`, Drizzle `sql.raw()`.
3. Dynamic identifiers that can't be parameterized: ORDER BY column, sort direction, table/column names, LIMIT from input.
4. NoSQL: request JSON straight into queries (operator injection like `{"$ne": null}`, `{"$gt": ""}`).
5. Supabase/PostgREST: filter strings from input, e.g. `` .or(`name.eq.${input}`) ``; `.rpc()` functions building dynamic SQL with `EXECUTE`.
6. Command injection: `exec`, `spawn` with `shell: true`, `os.system`, `subprocess(..., shell=True)`, any shell command with user input.

**Fix**
- Convert to parameterized queries/bound params or safe query builders.
- Dynamic identifiers → map to a hard-coded allowlist (`sort=price` → `"price"`).
- NoSQL: enforce input types before queries.
- Shell: argument arrays without a shell, or remove the need.
- DB user has only needed privileges.

**Verify:** tests sending `' OR '1'='1`, `'; DROP TABLE users; --`, `{"$ne": null}` to each affected input → normal empty/400, never extra data or DB errors.

**Watch out:** Prisma `$queryRaw` vs `$queryRawUnsafe` look almost identical. DB error messages help attackers (check 20).

**Done when**
- [ ] No query built by string concatenation with user input.
- [ ] Raw ORM calls with user input are parameterized or removed.
- [ ] Sort/column inputs go through an allowlist.
- [ ] Injection payloads return normal empty/400 responses.

---

## 18 · Restrict file uploads · HIGH

Goal: only expected files of reasonable size, stored and served so they can't execute.

**Self-check:** rename `.html` → `.jpg`, upload, open the URL (renders as a page?). Upload a file over the stated limit. Upload an SVG containing `<script>alert(1)</script>` and open it directly.

**Audit**
1. Every upload path: forms, avatars, attachments, CSV/Excel imports, drag-and-drop, presigned/direct-to-storage (S3, R2, Supabase Storage, Firebase Storage, UploadThing, Cloudinary), AI features accepting files.
2. Per path: auth required? which checks and where (client only or server)? storage location, naming, serving (domain, Content-Type, Content-Disposition), public?

**Fix** (enforced on the server or in storage policies, never browser-only)
1. Type allowlist per feature (e.g. avatars: jpeg, png, webp). Check extension AND real content via magic bytes (e.g. `file-type`); don't trust client Content-Type. Block HTML, SVG, XML, JS, executables unless truly needed.
2. Size cap per file (e.g. 5 MB images), server-side and in presigned conditions (`content-length-range`) or bucket limits; max files per request; per-user storage quota.
3. Random names (UUIDs); never the user's filename in storage paths (prevents `../` traversal); keep original name only as escaped display text.
4. Object storage or folder outside web root, private by default; private files via short-lived signed URLs after an authorization check.
5. Serving: correct Content-Type, `X-Content-Type-Options: nosniff`, `Content-Disposition: attachment` for non-display files; ideally a separate domain for user files.
6. Images: re-encode with sharp/Pillow (strips payloads and EXIF incl. GPS); cap pixel dimensions (decompression bombs).
7. Archives: cap uncompressed size and file count. CSV exports: prefix cells starting with `=`, `+`, `-`, `@` (formula injection).
8. Files shared between users: malware scan, or recommend a service.

**Verify:** tests uploading a renamed `.html`, a script-bearing `.svg`, an oversized file and a `../` filename → all rejected or neutralized.

**Watch out:** presigned uploads skip your server, so limits must live in the presigned policy or bucket rules. Public buckets are often listable.

**Done when**
- [ ] Allowed types checked by real content, not just extension.
- [ ] Size limits enforced on server or in storage.
- [ ] Files get random names and can't escape their folder.
- [ ] Uploaded files can't execute as pages on the main domain.
- [ ] Images re-encoded and location data stripped.

---

## 19 · Verify prices and payments · CRITICAL

Goal: the server decides what things cost; only a verified payment unlocks anything.

**Self-check:** edit price/amount/quantity in the checkout request → charged amount unchanged. Visit the success/thank-you URL directly without paying → nothing unlocks. Apply the same coupon twice, an expired coupon, quantity `0` or `-1`.

**Audit:** trace the whole money flow: product/plan pages → cart → checkout → provider (Stripe, Lemon Squeezy, Paddle, PayPal, Razorpay, RevenueCat…) → success page → webhook → fulfilment/entitlement → refunds/cancellations. At each step: what the client sends vs what the server trusts.

**Fix**
1. Client sends only product/plan IDs and quantities. Server looks up prices (DB or provider price IDs) and computes totals, tax, shipping, discounts. Ignore client price/amount/currency/total.
2. Quantities: integers, min 1, sensible max.
3. Money as integers in minor units; never floats.
4. Coupons/credits: validated server-side (exists, not expired, usage limits, per-user limits, eligible products) and applied inside a DB transaction (no double use via parallel requests).
5. Fulfil ONLY from verified webhooks (e.g. Stripe `checkout.session.completed`, `payment_intent.succeeded`, `invoice.paid`), never from the success redirect; success page only shows status.
6. Webhooks: verify signature with the RAW body + endpoint secret (e.g. `stripe.webhooks.constructEvent`); reject failures; store processed event IDs (idempotency); handle out-of-order events; check paid amount and currency match the order.
7. Subscriptions/entitlements: access decided on server from webhook-stored status, never a client flag or `?plan=pro`. Handle cancellations, failed payments, refunds, disputes (remove access).
8. Balances, credits, stock: atomic updates in transactions (no race double-spend).
9. Card data never touches the server; use hosted checkout/elements.
10. Test keys in dev, live only in prod; webhook route exempt from CSRF but signature-verified.

**Verify:** tests: tampered price, negative quantity, reused coupon, success URL without paying, unsigned/forged webhook, same webhook twice. Give provider CLI/dashboard steps for test webhooks (e.g. `stripe listen` / `stripe trigger`).

**Watch out:** parsing the webhook body as JSON before verifying breaks signatures (configure raw body on that route). Free trials and referrals are business-logic money leaks; ensure they can't be farmed with new emails.

**Done when**
- [ ] Totals computed only on the server from trusted prices.
- [ ] Orders/plans unlock only from signature-verified webhooks.
- [ ] Duplicate webhooks don't double-fulfil.
- [ ] Coupons, credits and stock can't be double-spent.
- [ ] Refunds and cancellations remove access.
