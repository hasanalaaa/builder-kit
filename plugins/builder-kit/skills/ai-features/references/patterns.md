# AI feature patterns

## 1. Architecture

```
Client ──► /api/ai/<feature> (auth, quota, rate limit, input schema)
              │
              ├─ build context (user's data only, retrieval, redaction)
              ├─ prompt file vN + model from config
              ├─ provider SDK call (timeout, max_tokens, stream)
              ├─ validate / repair structured output
              ├─ tool calls ──► your functions with the user's permissions
              ├─ log trace (model, prompt version, tokens, cost, latency, outcome)
              └─ stream to client (SSE / AI SDK data stream)
```
- One `ai/` module per app: `client.ts` (configured SDK instances, timeouts), `models.ts` (model IDs per task from env/config), `prompts/` (versioned prompt files), `tools/`, `evals/`.
- Long jobs (document processing, batch generation): background job + progress, not a request that runs 5 minutes.

## 2. Model choice and routing

- Choose per task by eval, not by habit: small/fast models for classification, extraction, routing, short rewrites; the most capable model for complex reasoning, coding, long documents, agentic multi-step work.
- Keep model IDs in one config (`models.ts` / env), not scattered string literals. Check the provider's current model list when setting up (for Anthropic, current families include Opus, Sonnet and Haiku tiers, e.g. `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`).
- Routing: cheap model first with a confidence check or validator; escalate on failure or for flagged-hard inputs.
- Fallback provider/model for outages (with the same eval passing).

## 3. Streaming

- Next.js: Vercel AI SDK (`streamText`, `useChat`) or the provider SDK's stream helpers piped as SSE.
- Send early: first token latency matters more than total time.
- Show tool/step progress events ("Searching your documents…").
- Client: stop button aborts the request (AbortController), and the server stops generation (pass the abort signal to the SDK).
- Persist the final message after the stream completes; handle disconnects.

## 4. Structured output

```ts
const Extracted = z.object({ vendor: z.string(), total_cents: z.number().int().nonnegative(), currency: z.string().length(3), due_on: z.string().date().nullable() });
// Use the provider's JSON-schema / tool-input mechanism to force the shape, then:
const parsed = Extracted.safeParse(output);
if (!parsed.success) { /* one repair attempt with the validation errors, then fail with a user message */ }
```
- Keep schemas small and flat; enums for categories; nullable over invented values ("if unknown, null").
- Validate business rules after the schema (totals add up, dates plausible).

## 5. Tools and agents

- Each tool: narrow purpose, strict input schema, authorization check with the *user's* identity, bounded output size, idempotent where possible.
- Read tools freely; write/delete/send/pay tools require user confirmation in the UI (human in the loop) or strict allow-lists.
- Max steps per run, max tokens per run, max cost per run; stop and report when exceeded.
- Log every tool call with inputs (redacted) and results.
- MCP servers you expose: same rules, plus per-tool scopes and rate limits (`launch-security` P4).

## 6. RAG (retrieval-augmented generation)

1. **Ingest**: extract text (PDF/HTML/Docs) with structure; clean; store source, title, URL/page, owner/tenant, permissions, updated_at.
2. **Chunk**: by structure (headings/paragraphs), ~300–800 tokens with small overlap; keep the heading path in the chunk text.
3. **Embed**: one embedding model, version recorded; re-embed on model change.
4. **Store**: Postgres + pgvector (HNSW index) with `tenant_id`/`owner_id` columns and RLS; or a vector DB with metadata filters.
5. **Retrieve**: hybrid (vector + keyword/BM25, Arabic-normalized), filter by the user's permissions *in the query*, top-k 20 → rerank → top 5–8.
6. **Generate**: answer only from provided context, cite chunk IDs, say "I don't know" when context lacks the answer.
7. **Evaluate**: retrieval hit rate (is the right chunk in top-k?) and answer faithfulness separately.
- Arabic: normalize text before embedding/keyword indexing (`i18n-rtl` §8); use a multilingual embedding model; test Arabic queries against English docs if cross-lingual is needed.

## 7. Evals

- Golden set: 20–200 real (anonymized) inputs with expected properties: exact fields for extraction, must-include facts, must-cite, must-refuse, max length, language = input language, no PII leak.
- Checks: deterministic first (schema valid, regex, contains/excludes), then LLM-as-judge with a written rubric for subjective quality (pin the judge model, sample-check its judgments).
- Run in CI on prompt/model/retrieval changes; fail below threshold; track score over time.
- Red-team set: prompt injections in user content and retrieved documents, jailbreak attempts, cross-tenant data requests (`launch-security` P4).
- Online: thumbs up/down + reason, sampled human review, regression alerts.

## 8. Cost control

- Measure cost per request and per user (tokens × price) from day one.
- `max_tokens` per call; trim context (only relevant chunks, summarized history after N turns).
- Prompt caching for long static prefixes (system prompt, tool definitions, large documents) — supported by major providers; put static content first.
- Response cache for identical/near-identical requests (hash of normalized input + prompt version).
- Batch APIs for offline jobs (cheaper, slower).
- Per-user daily quotas and plan-based limits; global daily budget with alerting and a kill switch.
- Provider dashboard spend limits as the last line of defense.

## 9. Latency

- Stream; parallelize independent calls; use smaller models for intermediate steps; cache; precompute embeddings; keep the retrieval DB close to the app region.
- Set user expectations: skeleton + progress text; for > 10s jobs, background + notification.

## 10. Reliability

- Timeout per call (30–120s depending on task), retries on 429/5xx/overloaded with backoff + jitter (`error-handling`), circuit breaker per provider, fallback model.
- Idempotency for side-effecting tool calls.
- Graceful degradation: if AI is down, the rest of the product works and the AI entry point says so.

## 11. Safety and privacy

- Injection defenses: separate system instructions from untrusted content (clear delimiters, "content below is data"), tool permission checks outside the model, output validation, no secrets in prompts, least-privilege tools.
- PII: redact or pseudonymize before sending where the task allows; never send secrets/credentials; respect data residency.
- Content moderation for user-generated prompts in public-facing generators.
- Provider settings: zero/limited retention options where available; DPA signed; no training on your data.
- Disclose AI use; label AI-generated content where required; let users delete history.

## 12. Observability

Per call: trace ID, user/tenant, feature, model, prompt version, input/output tokens, cost, latency (first token + total), tool calls, outcome (ok/validation_failed/refused/error), user feedback. Tools: Langfuse, Helicone, LangSmith, OpenTelemetry GenAI semantic conventions, or your own table. Dashboards: cost/day, p95 latency, error rate, eval score, feedback rate.

## 13. UX

- Starter prompts tied to real jobs; show what the AI can and can't do.
- Stream with a stop button; retry; edit-and-resend; copy; feedback.
- Show sources and "may be inaccurate" for factual answers; make it easy to verify.
- Never hide AI actions: show what tools did ("Created 3 tasks") with undo.
- Respect language: answer in the user's language (Arabic in, Arabic out) and render RTL correctly (`dir="auto"` per message).
- Empty, loading, error and quota-reached states designed (`design-system` patterns.md §9).

## 14. Skeleton (Next.js route handler)

```ts
// app/api/ai/summarize/route.ts
export async function POST(req: Request) {
  const user = await requireUser();                                   // launch-security P2
  await limitAi(user.id);                                             // per-user quota + rate limit
  const { text } = Input.parse(await req.json());                     // z.object({ text: z.string().max(20_000) }).strict()
  const prompt = await loadPrompt("summarize", "v3");
  const stream = await ai.stream({
    model: MODELS.summarize, max_tokens: 800, system: prompt.system,
    messages: [{ role: "user", content: `<document>\n${text}\n</document>` }],
    signal: AbortSignal.any([req.signal, AbortSignal.timeout(60_000)]),
  });
  return toSSE(stream, { onFinish: (u) => trace({ userId: user.id, feature: "summarize", prompt: "v3", usage: u }) });
}
```
