import Stripe from 'stripe';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fakeDb, freshDb } from '@/test/fake-db';
import { POST } from '@/app/api/webhooks/stripe/route';

vi.mock('@/lib/db', async () => (await import('@/test/fake-db')).fakeDb);

const SECRET = 'whsec_test_only';
const signer = new Stripe('test-only-not-a-key');

function event(id: string, type: string, session: Record<string, unknown>) {
  return {
    id, object: 'event', type,
    data: { object: { id: 'cs_1', object: 'checkout.session', client_reference_id: 'user_a', metadata: { credits: '100' }, ...session } },
  };
}

function deliver(payload: object, signature?: string) {
  const body = JSON.stringify(payload);
  const header = signature ?? signer.webhooks.generateTestHeaderString({ payload: body, secret: SECRET });
  return POST(new Request('http://test/api/webhooks/stripe', { method: 'POST', body, headers: { 'stripe-signature': header } }));
}

async function balance(userId = 'user_a') {
  const { rows } = await fakeDb.db.query<{ credits: string }>('select credits from credit_balances where user_id = $1', [userId]);
  return rows[0] ? Number(rows[0].credits) : 0;
}

beforeEach(async () => {
  vi.stubEnv('STRIPE_SECRET_KEY', 'test-only-not-a-key');
  vi.stubEnv('STRIPE_WEBHOOK_SECRET', SECRET);
  await freshDb('db/migrations/stripe_webhook.sql');
});

describe('POST /api/webhooks/stripe', () => {
  it('adds credits once for a paid checkout, even when Stripe delivers the event twice', async () => {
    const paid = event('evt_1', 'checkout.session.completed', { payment_status: 'paid' });
    expect((await deliver(paid)).status).toBe(200);
    expect((await deliver(paid)).status).toBe(200);
    expect(await balance()).toBe(100);
  });

  it('rejects a bad or missing signature and changes nothing', async () => {
    const paid = event('evt_2', 'checkout.session.completed', { payment_status: 'paid' });
    expect((await deliver(paid, 't=1,v1=deadbeef')).status).toBe(400);
    const unsigned = await POST(new Request('http://test/api/webhooks/stripe', { method: 'POST', body: JSON.stringify(paid) }));
    expect(unsigned.status).toBe(400);
    expect(await balance()).toBe(0);
    expect((await fakeDb.db.query('select 1 from stripe_events')).rows).toHaveLength(0);
  });

  it('waits for async_payment_succeeded when checkout completes unpaid', async () => {
    await deliver(event('evt_3', 'checkout.session.completed', { payment_status: 'unpaid' }));
    expect(await balance()).toBe(0);
    await deliver(event('evt_4', 'checkout.session.async_payment_succeeded', { payment_status: 'paid' }));
    expect(await balance()).toBe(100);
  });

  it('returns 500 and records nothing when the session lacks the user, so the retry can succeed', async () => {
    const res = await deliver(event('evt_5', 'checkout.session.completed', { payment_status: 'paid', client_reference_id: null }));
    expect(res.status).toBe(500);
    expect((await fakeDb.db.query('select 1 from stripe_events')).rows).toHaveLength(0);
  });

  it('acknowledges unrelated events without granting anything', async () => {
    expect((await deliver(event('evt_6', 'customer.created', {}))).status).toBe(200);
    expect(await balance()).toBe(0);
  });
});
