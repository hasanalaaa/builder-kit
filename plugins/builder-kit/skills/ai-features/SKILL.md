---
name: ai-features
description: Load before writing code that calls an LLM (Claude, OpenAI, Gemini): chat, streaming, generation, extraction, embeddings/RAG, agents, MCP tools. Server-side calls, bounded cost, structured output, evals, prompt-injection defense. Triggers: AI, LLM, chatbot, RAG, agent, ذكاء اصطناعي, شات بوت.
---

# AI Features

An AI feature is a product feature with a probabilistic, expensive, slow, attackable dependency in the middle. Treat the model like an unreliable remote service: bound its cost and time, validate its output, never let it act beyond the user's rights, measure its quality with tests, and design the UI for streaming, uncertainty and failure.

| File | Use it for |
|------|-----------|
| `references/patterns.md` | Architecture, model choice and routing, streaming, structured output, tools/agents, RAG pipeline, prompts as code, evals, cost and latency control, reliability, safety and privacy, observability, UX, ready code skeletons |
| `scripts/ai_check.py` | Scan for AI keys in client code, LLM calls without max tokens / timeout, model output rendered as raw HTML, user input interpolated into system prompts, AI routes without rate limiting, model IDs hard-coded in many files |

Security of AI features (prompt injection, tool permissions, data leaks) is specified in `launch-security/references/platforms.md` P4 and B1; follow both.
Ready code: a streaming chat endpoint (Next.js, Anthropic SDK) starts from the tested `ai-chat-stream` recipe (`recipes` skill, `bk_add.py ai-chat-stream`).

## 1. Rules

1. **Server only.** Model API keys never reach browsers or app bundles. The client calls your endpoint; your endpoint authenticates the user, checks quota, calls the model.
2. **Every call is bounded**: `max_tokens`, timeout, retry policy, per-user and global spend limits, provider spend caps (`launch-security` B5).
3. **Structured output is validated.** Ask for JSON via the provider's structured-output/tool mechanism, parse with a schema (Zod/pydantic), repair or retry once, then fail gracefully.
4. **The model never gets more power than the user.** Tools run with the user's permissions, scoped to their data; destructive or costly tool actions need explicit user confirmation; untrusted content (web pages, documents, emails) is data, never instructions.
5. **Model output is untrusted input**: escape it (render markdown with a sanitizing renderer, never `dangerouslySetInnerHTML` of raw output), validate URLs, never `eval` it, never pass it into SQL/shell.
6. **Prompts are code**: versioned files, reviewed, tested by an eval set before change. Model and prompt version logged with each call.
7. **Quality is measured, not felt.** A golden set of real inputs with expected properties runs in CI; changes to prompts, models or retrieval must not drop the score.
8. **Stream to users**; show progress for multi-step work; let them stop, retry and edit; show sources for factual answers.
9. **Privacy by default**: send the minimum data, redact PII where possible, use provider settings that don't train on your data, state AI use and retention in the privacy policy, let users delete their conversations.
10. **Pick the smallest model that passes the eval**, route hard cases to a larger one, cache aggressively (prompt caching for long static prefixes, response caching for repeated questions).

## 2. Workflow

1. Spec the feature (`product-spec`): the job, inputs, expected outputs, what a wrong answer costs, latency target, cost per use ceiling.
2. Build the eval set first: 20–50 real examples with expected properties (`patterns.md` §7).
3. Implement the thinnest version: one server endpoint, one prompt file, structured output, streaming, timeouts, quota.
   Every chat/stream endpoint you write shows, in the code itself: `max_tokens` (AI SDK: `maxOutputTokens`), a timeout, the per-user quota/rate-limit check before the call, and the client stop button wired to an abort signal that reaches the provider call.
4. Run the eval; iterate prompt/retrieval/model until it passes; record cost and latency per call.
5. Add safety: injection tests (`launch-security` P4), PII redaction, output sanitization, tool permission checks.
6. Ship behind a flag; trace every call; watch cost, latency, error rate, feedback.
7. Run `python3 <skill>/scripts/ai_check.py .` and `launch-security/scripts/security_scan.py .` → 0 ERROR.

## 3. Done when

- [ ] Keys server-only; per-user quota + rate limit + provider spend cap set.
- [ ] Every call has max tokens, timeout, retry/fallback policy; structured outputs validated.
- [ ] Eval set in CI with a pass threshold; prompt and model versions tracked.
- [ ] Output rendered safely; tools scoped to the user with confirmation for risky actions; injection tests pass.
- [ ] Streaming UI with stop/retry/error states; sources shown where factual.
- [ ] Traces show model, prompt version, tokens, cost, latency per call; dashboards and alerts for spend.
- [ ] Privacy: data minimization, provider data settings, user deletion, policy updated.
