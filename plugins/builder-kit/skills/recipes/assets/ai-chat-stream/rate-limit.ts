import { HttpError } from '@/lib/http';

const WINDOW_MS = 60_000; // ADAPT: window and budget per user
const MAX_PER_WINDOW = 20;

const hits = new Map<string, { count: number; resetAt: number }>();

// TODO: per-process memory, so each server instance counts separately. Replace the body with a shared store
// (Upstash/Redis, launch-security P10) before running more than one instance or on serverless.
export async function checkRateLimit(key: string, now = Date.now()): Promise<void> {
  const hit = hits.get(key);
  if (!hit || hit.resetAt <= now) {
    if (hits.size > 10_000) for (const [k, v] of hits) if (v.resetAt <= now) hits.delete(k);
    hits.set(key, { count: 1, resetAt: now + WINDOW_MS });
    return;
  }
  hit.count += 1;
  if (hit.count > MAX_PER_WINDOW) {
    throw new HttpError(429, 'Too many requests', { retryAfterSec: Math.ceil((hit.resetAt - now) / 1000) });
  }
}
