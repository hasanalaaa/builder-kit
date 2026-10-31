---
name: api-contracts
description: Load before adding or changing an endpoint, route handler, server action, RPC/GraphQL, webhook or SDK. Naming, status codes, RFC 9457 errors, validation, pagination, idempotency, versioning, OpenAPI. Triggers: API, REST, endpoint, breaking change, تصميم API.
---

# API Contracts

An API is a promise. The front end, mobile apps already installed on phones, partners and AI agents all depend on its exact shape. Inside the repo, change freely and migrate every caller (global CLAUDE.md §4). Across the boundary, never break the promise without a version and a migration path.

| File | Use it for |
|------|-----------|
| `references/conventions.md` | Naming, methods, status codes, error format, validation, pagination, filtering/sorting, idempotency, concurrency, rate limits, versioning, OpenAPI, typed clients, webhooks, server actions / tRPC / GraphQL notes, checklists |

## 1. Rules

1. **Contract first, then code.** Write the request/response schema (Zod/pydantic/OpenAPI) before the handler. The schema is the validator, the type and the docs.
2. **Validate every input at the boundary**, reject unknown fields (`.strict()`), and never trust IDs, prices, roles or owner fields from the client (`launch-security` 03, 06, 19).
3. **One error shape everywhere** (`conventions.md` §3): `type`, `title`, `status`, `detail`, `code`, `errors[]` for fields, `requestId`. No stack traces (`launch-security` 20).
4. **Status codes mean what they say.** 400 validation, 401 not signed in, 403 signed in but not allowed, 404 not found or not yours, 409 conflict, 422 semantic rule broken, 429 rate limited, 5xx only for server faults.
5. **Every list is paginated and capped.** Cursor for feeds and large tables, offset for small admin lists. Max page size enforced server-side.
6. **Unsafe retries are safe.** POSTs that create money, orders, messages or jobs accept an `Idempotency-Key`; webhooks are deduplicated by event ID.
7. **Authorization on every handler**, with the owner scope in the query, not just a login check.
8. **Version public contracts.** URL major version (`/v1`) or dated header for public APIs; additive changes only within a version; deprecate with headers and a date before removing (`conventions.md` §9).
9. **Generate docs and clients from the source of truth** (OpenAPI from Zod/pydantic, typed client generated or shared types). Hand-written docs drift.
10. **Mobile clients can't be force-updated.** Any endpoint used by an installed app version is a published contract: keep old shapes working until that version's share is negligible, and ship a minimum-version check.

## 2. Workflow: new endpoint / server action

1. Read `SPEC.md` story + permissions matrix + existing API conventions in the repo (nearest sibling endpoint).
2. Define: path and method (or action name), auth requirement and roles, input schema, output schema, errors it can return, idempotency, rate limit, pagination.
3. Implement with the validated handler pattern (`launch-security/references/secure-patterns.md` P3): parse → authorize → act (owner-scoped) → map to response → errors through the one boundary.
4. Tests: happy path, each error status, other user's resource (404/403), invalid input (400), unauthenticated (401), idempotent retry, page limits (`testing-strategy`).
5. Update OpenAPI/docs and the typed client; note breaking-change risk.

## 3. Workflow: changing an existing contract

1. Find every consumer: front end, mobile versions in the wild, partners, webhooks subscribers, AI tools/MCP.
2. Additive change (new optional field, new endpoint) → ship.
3. Breaking change (remove/rename field, change type or meaning, new required input, different status codes) → new version or new field alongside, dual-support period, deprecation headers, communicate, remove after the date. Requires explicit approval (global CLAUDE.md §4).

## 4. Done when

- [ ] Input and output schemas exist and validate at runtime; unknown fields rejected.
- [ ] Errors use the shared format and correct status codes; no internals leak.
- [ ] AuthN + AuthZ + owner scoping on every handler; tests prove 401/403/404.
- [ ] Lists paginated with a server-side cap; filters/sorts whitelisted.
- [ ] Idempotency for unsafe retries that create value; rate limit on expensive or abusable endpoints.
- [ ] OpenAPI/types/docs regenerated; breaking changes versioned and approved.
