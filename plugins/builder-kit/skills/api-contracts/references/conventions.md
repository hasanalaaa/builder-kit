# API conventions

## 1. Resources and methods

- Nouns, plural, kebab-case: `/v1/invoices`, `/v1/invoices/{id}/line-items`. Max two levels of nesting; deeper → top-level resource with a filter.
- Actions that aren't CRUD: a sub-resource verb as POST: `POST /v1/invoices/{id}/send`, `POST /v1/subscriptions/{id}/cancel`.
- JSON field names: `camelCase` (JS clients) or `snake_case` (Python ecosystems) — one convention for the whole API.
- IDs as strings (UUID or prefixed `inv_…`); timestamps ISO 8601 UTC (`2026-10-31T09:00:00Z`); money as integer minor units + currency (`{"amount": 1999, "currency": "SAR"}`); enums as lowercase strings.

| Method | Use | Idempotent | Success |
|--------|-----|-----------|---------|
| GET | read | yes | 200 |
| POST | create / action | no (use Idempotency-Key) | 201 + Location (create), 200/202 (action) |
| PUT | full replace | yes | 200 |
| PATCH | partial update | should be | 200 |
| DELETE | remove | yes | 204 |

## 2. Status codes

| Code | When |
|------|------|
| 200 OK / 201 Created / 202 Accepted (async job) / 204 No Content | success |
| 400 Bad Request | malformed JSON, schema validation failure |
| 401 Unauthorized | not authenticated / token expired |
| 403 Forbidden | authenticated but not allowed (use 404 to hide existence of others' resources) |
| 404 Not Found | doesn't exist or not visible to this user |
| 405 / 415 | wrong method / content type |
| 409 Conflict | duplicate, version conflict, state conflict (already paid) |
| 412 Precondition Failed | `If-Match` ETag mismatch |
| 422 Unprocessable Content | valid shape but business rule fails (end before start) |
| 429 Too Many Requests | rate limited, with `Retry-After` |
| 500 / 502 / 503 / 504 | server fault / upstream failure / maintenance / upstream timeout |

## 3. Error format (RFC 9457 problem details)

```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Invalid request",
  "status": 400,
  "detail": "2 fields are invalid.",
  "code": "validation_failed",
  "errors": [
    { "field": "email", "code": "invalid_format", "message": "Enter a valid email address." },
    { "field": "items[0].quantity", "code": "too_small", "message": "Quantity must be at least 1." }
  ],
  "requestId": "req_01J9…"
}
```
- `Content-Type: application/problem+json`.
- `code` is stable and machine-readable; `message` is human and may be localized (Accept-Language).
- Same shape from every handler: one error boundary maps exceptions to problems (`error-handling` skill).

## 4. Validation

- Parse with a schema library at the edge: Zod/Valibot (TS), pydantic (Python), and derive types from it.
- `.strict()` / `extra="forbid"`: unknown fields rejected (stops mass assignment).
- Bounds on everything: string lengths, array sizes, numeric ranges, enum membership, page size, upload size.
- Normalize: trim strings, lower-case emails, Unicode-normalize (NFC) text, convert Arabic-Indic digits if accepted.
- Server computes anything with trust value: prices, totals, roles, owner IDs, timestamps.

## 5. Pagination, filtering, sorting

Cursor pagination response:
```json
{ "data": [ … ], "pagination": { "nextCursor": "eyJpZCI6…", "hasMore": true } }
```
Request: `GET /v1/invoices?limit=20&cursor=…`. Default limit 20, max 100 (enforced).

Offset (small sets): `?page=2&pageSize=25` → `{ "data": [...], "pagination": { "page": 2, "pageSize": 25, "total": 312 } }`. Avoid `total` on huge tables (expensive count).

Filtering: explicit allowed params `?status=paid&createdAfter=2026-01-01`. Sorting: `?sort=-createdAt,number` with a whitelist of sortable fields. Never pass raw column names or operators into queries.

Search: `?q=` with server-side normalization; separate endpoint if it needs ranking.

## 6. Idempotency and concurrency

- `Idempotency-Key: <uuid>` header on POSTs that create value. Store `(key, user, request hash) → response` for 24h; same key + same body → replay stored response; same key + different body → 422.
- Optimistic concurrency: return `ETag` (version) on GET; require `If-Match` on PUT/PATCH for documents edited by several people → 412 on mismatch.
- Long operations: `202 Accepted` + `Location: /v1/jobs/{id}`; job resource with `status` and `result`.

## 7. Rate limits and quotas

- Per user + per IP for auth endpoints; per API key for public APIs; tighter on expensive endpoints (AI, exports, email sending).
- Headers: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` (or the combined `RateLimit` header), and `Retry-After` on 429.
- Implementation: `launch-security/references/secure-patterns.md` P10.

## 8. Caching

- `Cache-Control: no-store` for personal/authenticated data unless deliberately cached privately.
- Public, cacheable GETs: `Cache-Control: public, max-age=…, stale-while-revalidate=…` + `ETag`.
- Vary on `Authorization`/`Accept-Language` when responses differ.

## 9. Versioning and deprecation

- Public API: major version in the path (`/v1`). Inside a version only additive changes: new endpoints, new optional request fields, new response fields (clients must ignore unknown fields).
- Breaking change → `/v2` (or a dated version header) with both live during migration.
- Deprecation: `Deprecation: @<unix-ts>` and `Sunset: <http-date>` headers, `Link: <docs>; rel="deprecation"`, changelog entry, emails to key consumers, usage monitoring of the old version before removal.
- Mobile: send app version in a header (`X-App-Version`); a `/v1/config` endpoint returns `minSupportedVersion` so old apps show "please update" instead of breaking.

## 10. Documentation and clients

- OpenAPI 3.1 generated from code: `zod-openapi`/`@asteasolutions/zod-to-openapi`, Hono `@hono/zod-openapi`, NestJS Swagger, FastAPI (built in).
- Typed clients: `openapi-typescript` + `openapi-fetch`, or shared types in a monorepo, tRPC end-to-end types.
- Every endpoint documents auth, scopes/roles, request, response, errors, rate limit, examples.
- Changelog per version.

## 11. Outbound webhooks (your API notifying others)

- Event envelope: `{ "id": "evt_…", "type": "invoice.paid", "createdAt": "…", "data": { … } }`.
- Sign the raw body (HMAC-SHA256 with a per-endpoint secret) and include a timestamp; document verification; reject replays older than 5 minutes.
- Retry with exponential backoff for ~24–72h; at-least-once delivery; consumers dedupe by `id`.
- Endpoint management UI: URL, secret rotation, event types, delivery log, replay.
- Never send secrets or excessive personal data in payloads; send IDs and let consumers fetch.

## 12. Server actions, tRPC, GraphQL

- **Server actions (Next.js)**: they are public POST endpoints. Validate input with a schema, authorize inside the action, return typed results `{ ok: true, data } | { ok: false, error }`, revalidate paths/tags after mutation. Never trust hidden form fields.
- **tRPC**: input validators on every procedure; `protectedProcedure` middleware for auth; map errors to `TRPCError` codes consistently.
- **GraphQL**: depth/complexity limits, pagination via connections (cursor), DataLoader against N+1, field-level authorization, disable introspection in production for private APIs, persisted queries for public clients.

## 13. Review checklist (per endpoint)

- [ ] Name, method, status codes follow §1–2.
- [ ] Input schema strict + bounded; output schema excludes internals.
- [ ] AuthN, AuthZ, owner scoping; 401/403/404 tests.
- [ ] Errors in the shared format.
- [ ] Pagination with cap; whitelisted filters/sorts.
- [ ] Idempotency / concurrency control where needed.
- [ ] Rate limit where abusable or expensive.
- [ ] Docs/OpenAPI/types updated; breaking changes versioned.
