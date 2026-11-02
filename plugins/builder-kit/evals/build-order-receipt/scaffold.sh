#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'app/api/orders/[id]/pay' 'jobs' 'lib'
cat > 'package.json' <<'J'
{ "name": "shop", "private": true, "dependencies": { "next": "16.0.0", "pg": "8.13.0", "resend": "6.1.0" } }
J
cat > 'lib/db.ts' <<'J'
import { Pool } from "pg";
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// orders(id uuid pk, user_id uuid, customer_email text, currency char(3), total_cents int, status text)
// order_items(order_id uuid, name text, quantity int, unit_price_cents int)
// jobs(id bigserial, name text, payload jsonb, run_after timestamptz, attempts int)
J
cat > 'lib/email.ts' <<'J'
import { Resend } from "resend";
const resend = new Resend(process.env.RESEND_API_KEY);
export async function sendEmail(opts: { to: string; subject: string; html: string; text?: string; idempotencyKey?: string }) {
  const { error } = await resend.emails.send(
    { from: "Shop <orders@shop.example>", to: opts.to, subject: opts.subject, html: opts.html, text: opts.text },
    opts.idempotencyKey ? { idempotencyKey: opts.idempotencyKey } : undefined,
  );
  if (error) throw new Error(error.message);
}
J
cat > 'lib/queue.ts' <<'J'
import { pool } from "@/lib/db";
// Background jobs: enqueue() stores the job; the worker (scripts/worker.ts) runs jobs/<name>.ts and retries failures with backoff.
export async function enqueue(name: string, payload: Record<string, unknown>) {
  await pool.query("insert into jobs (name, payload, run_after, attempts) values ($1, $2, now(), 0)", [name, JSON.stringify(payload)]);
}
J
cat > 'lib/logger.ts' <<'J'
export const logger = {
  info: (msg: string, data?: Record<string, unknown>) => console.log(JSON.stringify({ level: "info", msg, ...data })),
  error: (msg: string, data?: Record<string, unknown>) => console.error(JSON.stringify({ level: "error", msg, ...data })),
};
J
cat > 'jobs/welcome-email.ts' <<'J'
import { pool } from "@/lib/db";
import { sendEmail } from "@/lib/email";
export default async function welcomeEmail({ userId }: { userId: string }) {
  const { rows } = await pool.query("select email from users where id = $1", [userId]);
  if (!rows[0]) return;
  await sendEmail({ to: rows[0].email, subject: "Welcome to Shop", html: "<p>Thanks for joining.</p>", text: "Thanks for joining." });
}
J
cat > 'app/api/orders/[id]/pay/route.ts' <<'J'
import { pool } from "@/lib/db";
export async function POST(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  // the payment provider has captured the payment before this is called
  const { rows } = await pool.query("update orders set status = 'paid' where id = $1 and status = 'pending' returning *", [id]);
  if (!rows[0]) return Response.json({ error: "not_found" }, { status: 404 });
  return Response.json(rows[0]);
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
