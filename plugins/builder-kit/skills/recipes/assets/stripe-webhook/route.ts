import Stripe from 'stripe';
import { tx, type Queryable } from '@/lib/db';
import { env } from '@/lib/env';

let stripe: Stripe | undefined;
const client = () => (stripe ??= new Stripe(env('STRIPE_SECRET_KEY')));

// Stripe → POST /api/webhooks/stripe. The success page never grants anything; this handler does.
export async function POST(req: Request) {
  const signature = req.headers.get('stripe-signature');
  if (!signature) return new Response('Missing signature', { status: 400 });
  const secret = env('STRIPE_WEBHOOK_SECRET');

  let event: Stripe.Event;
  try {
    event = client().webhooks.constructEvent(await req.text(), signature, secret); // raw body, not req.json()
  } catch {
    return new Response('Bad signature', { status: 400 });
  }

  try {
    await tx(async (db) => {
      const first = await db.query(
        'insert into stripe_events (event_id, type) values ($1, $2) on conflict (event_id) do nothing returning event_id',
        [event.id, event.type],
      );
      if (first.rows.length === 0) return; // already processed: a retry or a replay
      await fulfil(db, event);
    });
  } catch (e) {
    // Rolled back together with the event row, so Stripe's retry processes it again.
    console.error(JSON.stringify({ event: 'stripe_webhook_failed', eventId: event.id, error: String(e) }));
    return new Response('Webhook handler failed', { status: 500 });
  }
  return new Response(null, { status: 200 });
}

async function fulfil(db: Queryable, event: Stripe.Event) {
  // async_payment_succeeded: bank debits etc. complete later than checkout.
  if (event.type !== 'checkout.session.completed' && event.type !== 'checkout.session.async_payment_succeeded') return;
  const session = event.data.object;
  if (session.payment_status !== 'paid') return; // not paid yet: wait for async_payment_succeeded

  // ADAPT: set both when you create the Checkout Session on the server, from your own catalog:
  //   stripe.checkout.sessions.create({ ..., client_reference_id: user.id, metadata: { credits: String(pack.credits) } })
  const userId = session.client_reference_id;
  const credits = Number(session.metadata?.credits);
  if (!userId || !Number.isSafeInteger(credits) || credits <= 0) {
    throw new Error(`checkout session ${session.id} has no client_reference_id or credits metadata`);
  }
  await db.query(
    `insert into credit_balances (user_id, credits) values ($1, $2)
     on conflict (user_id) do update set credits = credit_balances.credits + excluded.credits, updated_at = now()`,
    [userId, credits],
  );
}
