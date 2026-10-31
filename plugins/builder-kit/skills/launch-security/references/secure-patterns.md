# Secure patterns: copy, don't reinvent

Security code written from scratch on every project is where first attempts go wrong. These are the small, proven building blocks behind the §2 rules. Start every sensitive feature from the matching pattern, adapt names to the project, and keep each block in its single home (see project-architecture's single-source-of-truth table).

Before using a snippet: confirm the package is already installed or is the real, maintained one, and check the API against the installed version (signatures change between majors). Snippets are TypeScript (Next.js App Router / Node) and Python (FastAPI); the same shape works in any stack.

| # | Pattern | Checks |
|---|---------|--------|
| P1 | Validated config, fail fast | 11 |
| P2 | `requireUser` / `requireAdmin` | 01, 09 |
| P3 | Validated handler + one error boundary | 06, 20, 08 |
| P4 | Ownership-scoped queries | 03, H2 |
| P5 | Supabase RLS policy set | 03 |
| P6 | Password hashing | 05 |
| P7 | One-time tokens (reset, magic link, invite) | 17 |
| P8 | Safe redirect | 01 |
| P9 | Same-origin check for state changes | 16 |
| P10 | Rate limit | 12 |
| P11 | Security headers | 14, 04 |
| P12 | Payment webhook | 19 |
| P13 | Upload check | 18 |
| P14 | Outbound fetch of user URLs | B2 |
| P15 | Security event log | 08 |
| P16 | Abuse tests that ship with the feature | 27 |

---

## P1 · Validated config, fail fast (11)

```ts
// src/server/env.ts — the only place that reads process.env
import 'server-only';
import { z } from 'zod';

const Env = z.object({
  DATABASE_URL: z.string().url(),
  SESSION_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith('whsec_'),
  APP_URL: z.string().url(),
});

export const env = Env.parse(process.env); // throws at startup naming the bad variable, never printing values
export const appOrigin = new URL(env.APP_URL).origin;
```

```python
# app/core/config.py
from pydantic import AnyHttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: SecretStr      # SecretStr keeps values out of logs and error messages
    session_secret: SecretStr
    app_url: AnyHttpUrl

    @field_validator("session_secret")
    @classmethod
    def long_enough(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("must be at least 32 characters")
        return v

settings = Settings()
```
No fallbacks (`?? 'dev-secret'`). Missing config is a startup crash, not a silent default.

---

## P2 · requireUser / requireAdmin (01, 09)

```ts
// src/server/auth.ts
import 'server-only';
import { createServerSupabase } from '@/server/supabase'; // wraps createServerClient from @supabase/ssr

export class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function requireUser() {
  const supabase = await createServerSupabase();
  const { data: { user }, error } = await supabase.auth.getUser(); // re-validates with the auth server
  if (error || !user) throw new HttpError(401, 'Unauthorized');
  return user;
}

export async function requireAdmin() {
  const user = await requireUser();
  if (user.app_metadata?.role !== 'admin') throw new HttpError(403, 'Forbidden'); // never user_metadata
  return user;
}
```
Other providers: same two functions, backed by the provider's server-side verification (Clerk `auth()`, Auth.js `auth()`, Firebase Admin `verifyIdToken`). Call one of them on the first line of every protected handler, server action and route.

```python
# app/core/security.py
import jwt  # PyJWT
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer(auto_error=False)

def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if creds is None:
        raise HTTPException(401, "Unauthorized")
    try:
        return jwt.decode(creds.credentials, PUBLIC_KEY, algorithms=["RS256"],  # explicit allowlist, never "none"
                          audience=AUDIENCE, issuer=ISSUER)
    except jwt.PyJWTError:
        raise HTTPException(401, "Unauthorized")

def require_admin(user: dict = Depends(current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(403, "Forbidden")
    return user
```

---

## P3 · Validated handler + one error boundary (06, 20, 08)

```ts
// src/server/http.ts
import 'server-only';
import { HttpError } from '@/server/auth';
import { logSecurityEvent } from '@/server/log';

export function handleError(e: unknown, requestId: string) {
  if (e instanceof HttpError) {
    if (e.status === 401 || e.status === 403) logSecurityEvent('permission_denied', { requestId, status: e.status });
    return Response.json({ error: e.message, requestId }, { status: e.status });
  }
  console.error(JSON.stringify({ requestId, error: String(e) })); // details stay in server logs
  return Response.json({ error: 'Something went wrong', requestId }, { status: 500 });
}
```

```ts
// src/features/orders/api.ts (called from app/api/orders/route.ts)
import { z } from 'zod';

const CreateOrder = z.object({
  productId: z.string().uuid(),
  quantity: z.number().int().min(1).max(100),
}).strict(); // unknown fields (role, price, userId…) are rejected

export async function POST(req: Request) {
  const requestId = crypto.randomUUID();
  try {
    const user = await requireUser();
    assertSameOrigin(req);                                   // P9
    const parsed = CreateOrder.safeParse(await req.json().catch(() => null));
    if (!parsed.success) {
      return Response.json({ error: 'Invalid input', fields: parsed.error.flatten().fieldErrors, requestId }, { status: 400 });
    }
    const order = await createOrder(user.id, parsed.data);  // price looked up on the server
    return Response.json(order, { status: 201 });
  } catch (e) {
    return handleError(e, requestId);
  }
}
```
Every handler has this same shape: identity → origin → validate → one use case → map result. Nothing else.

---

## P4 · Ownership-scoped queries (03, H2)

```ts
// Read, update and delete always include the owner in the WHERE clause.
const order = await db.order.findFirst({ where: { id, userId: user.id } });
if (!order) throw new HttpError(404, 'Not found'); // 404, not 403: don't confirm the ID exists

await db.order.updateMany({ where: { id, userId: user.id }, data: { note } }); // count 0 → 404
```
Multi-tenant apps: replace `userId: user.id` with `orgId: membership.orgId`, where the membership comes from the session, never from the request.

---

## P5 · Supabase RLS policy set (03)

```sql
-- supabase/migrations/<timestamp>_orders.sql
create table public.orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  note text check (char_length(note) <= 500),
  created_at timestamptz not null default now()
);

alter table public.orders enable row level security;

create policy "orders: owner reads"   on public.orders for select to authenticated
  using ((select auth.uid()) = user_id);
create policy "orders: owner inserts" on public.orders for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy "orders: owner updates" on public.orders for update to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "orders: owner deletes" on public.orders for delete to authenticated
  using ((select auth.uid()) = user_id);

create index on public.orders (user_id); -- policies filter on it
```
Every new table ships in the same migration as its `enable row level security` and its four policies. `(select auth.uid())` is evaluated once per query (faster than calling `auth.uid()` per row). Views: `with (security_invoker = true)`.

---

## P6 · Password hashing (05), only if you store passwords yourself

```ts
import argon2 from 'argon2';
const hash = await argon2.hash(password, { type: argon2.argon2id, memoryCost: 19456, timeCost: 2, parallelism: 1 }); // 19 MiB
const ok = await argon2.verify(hash, password);
```
```python
from argon2 import PasswordHasher
ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
hash_ = ph.hash(password)
ph.verify(hash_, password)  # raises on mismatch
```
Prefer an auth provider, which removes this code entirely.

---

## P7 · One-time tokens: reset, magic link, invite (17)

```ts
import { randomBytes, createHash } from 'node:crypto';

export function newToken() {
  const token = randomBytes(32).toString('base64url');                 // goes in the emailed link only
  const tokenHash = createHash('sha256').update(token).digest('hex');  // the only thing stored
  return { token, tokenHash };
}
// Store { userId, tokenHash, expiresAt: now + 30 min, usedAt: null }; delete older tokens for the user.
// Redeem: hash the presented token, find an unexpired + unused row, mark used in the same transaction.
// Link: `${env.APP_URL}/reset?token=${token}`, never built from the Host header.
```

---

## P8 · Safe redirect (01)

```ts
export function safeNext(next: string | null, fallback = '/') {
  if (!next || !next.startsWith('/') || next.startsWith('//') || next.startsWith('/\\')) return fallback;
  return next; // same-site path only
}
```

---

## P9 · Same-origin check for state changes (16)

```ts
export function assertSameOrigin(req: Request) {
  const origin = req.headers.get('origin');
  if (origin && origin !== appOrigin) throw new HttpError(403, 'Bad origin');
}
```
Use it in every POST/PUT/PATCH/DELETE handler that relies on cookies, on top of SameSite=Lax cookies. Next.js Server Actions already compare Origin and Host; don't loosen `serverActions.allowedOrigins`.

---

## P10 · Rate limit (12)

```ts
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const redis = Redis.fromEnv();
export const limits = {
  login: new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(5, '1 m'), prefix: 'rl:login' }),
  ai: new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(20, '1 m'), prefix: 'rl:ai' }),
};

export async function enforce(limit: Ratelimit, key: string) {
  const { success, reset } = await limit.limit(key);
  if (!success) {
    throw Object.assign(new HttpError(429, 'Too many requests'), {
      retryAfter: Math.ceil((reset - Date.now()) / 1000),
    }); // handleError adds the Retry-After header
  }
}
```
Key by user ID when signed in, otherwise by the platform's verified client IP (+ email for login).

---

## P11 · Security headers (14, 04)

```js
// next.config.js
const securityHeaders = [
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
];

module.exports = {
  poweredByHeader: false,
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },
};
```
Add the CSP with per-request nonces in middleware, following the framework's current CSP guide, report-only first. Express: `app.use(helmet())`. FastAPI: a small middleware that sets the same headers. Verify on the live URL with `scripts/check-headers.sh`.

---

## P12 · Payment webhook (19)

```ts
// app/api/webhooks/stripe/route.ts
export async function POST(req: Request) {
  const signature = req.headers.get('stripe-signature');
  if (!signature) return new Response('Missing signature', { status: 400 });

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(await req.text(), signature, env.STRIPE_WEBHOOK_SECRET); // raw body
  } catch {
    return new Response('Bad signature', { status: 400 });
  }

  const firstTime = await markEventProcessed(event.id); // insert into processed_events (unique id); false if it existed
  if (firstTime) await fulfil(event);                   // fulfilment happens here, never on the success page
  return new Response(null, { status: 200 });
}
```

---

## P13 · Upload check (18)

```ts
import { fileTypeFromBuffer } from 'file-type';

const ALLOWED = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_BYTES = 5 * 1024 * 1024;

export async function checkImage(buf: Uint8Array) {
  if (buf.byteLength > MAX_BYTES) throw new HttpError(413, 'File too large');
  const type = await fileTypeFromBuffer(buf);           // real content, not the extension
  if (!type || !ALLOWED.has(type.mime)) throw new HttpError(415, 'Unsupported file type');
  return { ext: type.ext, key: `${crypto.randomUUID()}.${type.ext}` }; // random name, never the user's
}
```
Then re-encode images (sharp) and store privately; serve through short-lived signed URLs.

---

## P14 · Outbound fetch of user-supplied URLs (B2)

```python
import ipaddress, socket
from urllib.parse import urlparse

def assert_public_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("Only http(s) URLs are allowed")
    for info in socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80)):
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ValueError("Address not allowed")
```
Disable automatic redirects and re-check every hop; set a timeout and a response size cap. To defeat DNS rebinding, connect to the IP you checked (or use a maintained SSRF-filtering HTTP agent for the stack).

---

## P15 · Security event log (08)

```ts
// src/server/log.ts
const REDACT = /pass(word)?|token|secret|authorization|cookie|api[-_]?key/i;

export function logSecurityEvent(event: string, details: Record<string, unknown>) {
  const safe = Object.fromEntries(
    Object.entries(details).map(([k, v]) => [k, REDACT.test(k) ? '[redacted]' : String(v).replace(/[\r\n]/g, ' ')]),
  );
  console.log(JSON.stringify({ ts: new Date().toISOString(), event, ...safe }));
}
```
Ship stdout to a log service with retention and alerts (08).

---

## P16 · Abuse tests that ship with the feature (27)

Every sensitive feature lands with its "try to break it" tests in the same change:

```ts
// orders.security.test.ts (Vitest + a test client; adapt to the project's runner)
it('rejects signed-out requests', async () => {
  expect((await api.post('/api/orders', valid)).status).toBe(401);
});
it("hides other users' orders", async () => {
  const res = await api.as(userB).get(`/api/orders/${orderOfUserA.id}`);
  expect(res.status).toBe(404);
});
it('ignores client-sent price and role', async () => {
  const res = await api.as(userA).post('/api/orders', { ...valid, price: 1, role: 'admin' });
  expect(res.status).toBe(400); // strict schema
});
it('rejects a foreign origin', async () => {
  const res = await api.as(userA).post('/api/orders', valid, { headers: { origin: 'https://evil.example' } });
  expect(res.status).toBe(403);
});
```
Minimum set per feature: signed-out → 401, other user's object → 404, tampered or extra fields → 400, foreign origin → 403, over the rate limit → 429.
