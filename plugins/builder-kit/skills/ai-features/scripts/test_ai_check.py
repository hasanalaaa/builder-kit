#!/usr/bin/env python3
"""Self-test for ai_check. Run: python3 test_ai_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai_check  # noqa: E402

BAD = {
    "app/chat/page.tsx": ("'use client'\nimport Anthropic from '@anthropic-ai/sdk'\n"
                          "const c = new Anthropic({ apiKey: process.env.NEXT_PUBLIC_ANTHROPIC_KEY })\n"
                          "const r = await c.messages.create({ model: 'claude-x-1', messages })\n"
                          "export default () => <div dangerouslySetInnerHTML={{ __html: answer }} />\n"),
    "app/api/ai/route.ts": ("import OpenAI from 'openai'\nconst o = new OpenAI()\n"
                            "export async function POST(req) {\n  const r = await o.chat.completions.create({\n"
                            "    model: 'gpt-x-1',\n    messages: [{ role: 'system', content: `You help ${user.name}` }],\n  })\n}\n"),
    "lib/a.ts": "import { generateText } from 'ai'\nconst m = 'claude-y-2'\n",
    "lib/b.ts": "import { generateText } from 'ai'\nconst m = 'claude-y-3'\n",
}
GOOD = {
    "app/api/ai/route.ts": ("import Anthropic from '@anthropic-ai/sdk'\nimport { MODELS } from '@/ai/models'\n"
                            "const c = new Anthropic({ timeout: 60_000 })\n"
                            "export async function POST(req) {\n  await ratelimit.limit(user.id)\n"
                            "  return c.messages.stream({ model: MODELS.chat, max_tokens: 800, system: PROMPT, messages })\n}\n"),
    "app/chat/page.tsx": "'use client'\nexport default () => <Markdown>{answer}</Markdown>\n",
}


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in ai_check.run(d)}


if __name__ == "__main__":
    got = run_on(BAD)
    want = {"ai-key-public", "raw-model-html", "ai-call-client", "no-max-tokens", "no-timeout",
            "system-prompt-interp", "ai-route-no-limit", "scattered-models"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD)
    assert not got, sorted(got)
    print("selftest OK")
