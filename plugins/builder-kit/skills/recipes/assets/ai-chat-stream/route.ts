import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';
import { requireUser } from '@/lib/auth';
import { env } from '@/lib/env';
import { handleError, HttpError, readJson } from '@/lib/http';
import { checkRateLimit } from '@/lib/rate-limit';

const MODEL = 'claude-sonnet-5-5'; // ADAPT: the smallest model that passes your eval
const MAX_TOKENS = 4096;
const TIMEOUT_MS = 120_000;
const MAX_TOTAL_CHARS = 32_000;
// ADAPT: your prompt. Static text only: user input goes in `messages`, never into the system prompt.
const SYSTEM = 'You are a helpful assistant. Answer concisely.';

const Body = z.object({
  messages: z.array(z.object({
    role: z.enum(['user', 'assistant']),
    content: z.string().min(1).max(8_000),
  }).strict()).min(1).max(40),
}).strict();

let anthropic: Anthropic | undefined;
const client = () => (anthropic ??= new Anthropic({ apiKey: env('ANTHROPIC_API_KEY') })); // server-only env var

// POST /api/chat { messages } → text/plain stream of the reply. The browser never sees the API key.
export async function POST(req: Request) {
  const requestId = crypto.randomUUID();
  try {
    const user = await requireUser();
    await checkRateLimit(`chat:${user.id}`); // before any model spend
    const { messages } = await readJson(req, Body);
    if (messages.at(-1)?.role !== 'user') throw new HttpError(400, 'Last message must be from the user');
    if (messages.reduce((n, m) => n + m.content.length, 0) > MAX_TOTAL_CHARS) throw new HttpError(413, 'Conversation too long');

    const stream = client().messages.stream(
      { model: MODEL, max_tokens: MAX_TOKENS, system: SYSTEM, messages, output_config: { effort: 'low' } },
      // Client disconnect (req.signal) or the timeout aborts the upstream call, so generation and billing stop.
      { signal: AbortSignal.any([req.signal, AbortSignal.timeout(TIMEOUT_MS)]) },
    );

    const encoder = new TextEncoder();
    let cancelled = false;
    const body = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          for await (const event of stream) {
            if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
              controller.enqueue(encoder.encode(event.delta.text));
            }
          }
          const { usage, stop_reason } = await stream.finalMessage();
          // ADAPT: send to your structured logger / tracing. Cost per user and call needs these fields.
          console.info(JSON.stringify({ requestId, userId: user.id, model: MODEL, stop_reason, usage })); // bk-ignore: console-in-server
          controller.close();
        } catch (e) {
          if (!cancelled) console.error(JSON.stringify({ requestId, error: String(e) }));
          controller.error(e);
        }
      },
      cancel() {
        cancelled = true;
        stream.abort();
      },
    });
    return new Response(body, { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' } });
  } catch (e) {
    return handleError(e, requestId);
  }
}
