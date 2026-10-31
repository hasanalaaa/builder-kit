#!/usr/bin/env python3
"""ai_check: scan for risky or costly patterns in code that calls LLM providers.

Usage: ai_check.py [root]
Each finding: LEVEL rule path:line  message. Exit 1 on any ERROR.
Silence a line with "ai-check: ignore"; a file with "ai-check: ignore-file".
"""
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".vue", ".svelte")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "__pycache__", ".turbo"}
TEST = re.compile(r"(\.test\.|\.spec\.|__tests__|/tests?/|test_\w+\.py$|evals?/)")

PUBLIC_KEY = re.compile(r"(NEXT_PUBLIC|VITE|EXPO_PUBLIC|REACT_APP|NUXT_PUBLIC|PUBLIC)_\w*(OPENAI|ANTHROPIC|CLAUDE|GEMINI|GOOGLE_AI|GROQ|MISTRAL|COHERE|DEEPSEEK|OPENROUTER|XAI)\w*")
AI_CALL = re.compile(r"(messages\.create|messages\.stream|chat\.completions\.create|responses\.create|completions\.create|generateText|streamText|generateObject|streamObject|generate_content|ChatCompletion\.create)\s*\(")
AI_IMPORT = re.compile(r"(@anthropic-ai/sdk|from ['\"]openai['\"]|import openai|from openai|import anthropic|from anthropic|['\"]ai['\"]|@ai-sdk/|@google/genai|google\.genai|google\.generativeai|langchain|llamaindex)")
MAX_TOK = re.compile(r"max_tokens|maxTokens|max_output_tokens|maxOutputTokens|max_completion_tokens")
TIMEOUT = re.compile(r"timeout|AbortSignal|signal\s*:|abortSignal")
RAW_HTML = re.compile(r"dangerouslySetInnerHTML\s*=\s*\{\{\s*__html\s*:\s*[^}]*(completion|response|answer|output|message|content|text|result|generated)", re.I)
VHTML = re.compile(r"v-html\s*=\s*\"[^\"]*(completion|response|answer|output|message|content|generated)", re.I)
SYSTEM_INTERP = re.compile(r"(system\s*:\s*`[^`]*\$\{|role\s*:\s*['\"]system['\"]\s*,\s*content\s*:\s*`[^`]*\$\{|system\s*=\s*f['\"])")
MODEL_LIT = re.compile(r"['\"]((?:claude|gpt|o\d|gemini|mistral|llama|deepseek|grok)[\w.\-]*\d[\w.\-]*)['\"]")
RATE = re.compile(r"rate.?limit|ratelimit|limiter|quota|Ratelimit|throttle", re.I)


def walk(root):
    return bk.walk(root, EXT, IGNORE_DIRS)


def call_window(lines, i, span=25):
    """Text of an AI call from line i until its parentheses balance (max span lines)."""
    depth, out = 0, []
    for line in lines[i:i + span]:
        out.append(line)
        depth += line.count("(") - line.count(")")
        if depth <= 0 and len(out) > 0 and "(" in "".join(out):
            break
    return "\n".join(out)


def scan(rel, text, findings, models):
    if "ai-check: ignore-file" in text:
        return
    test = bool(TEST.search(rel))
    lines = text.splitlines()
    client_side = rel.endswith((".tsx", ".jsx", ".vue", ".svelte")) and re.match(r"\s*['\"]use client['\"]", text)
    uses_ai = bool(AI_IMPORT.search(text) or AI_CALL.search(text))
    for n, line in enumerate(lines, 1):
        if "ai-check: ignore" in line:
            continue
        add = lambda level, rule, msg: findings.append(("WARN" if test else level, rule, rel, n, msg))
        if PUBLIC_KEY.search(line):
            add("ERROR", "ai-key-public", "AI provider key in a client-exposed env var: call the model from the server only")
        if RAW_HTML.search(line) or VHTML.search(line):
            add("ERROR", "raw-model-html", "Model output rendered as raw HTML (XSS): render sanitized markdown")
        if uses_ai and SYSTEM_INTERP.search(line):
            add("WARN", "system-prompt-interp", "Variable interpolated into the system prompt: keep untrusted input in user content with delimiters")
        if uses_ai:
            for m in MODEL_LIT.finditer(line):
                models[m.group(1)].append((rel, n))
        if AI_CALL.search(line) and not test:
            window = call_window(lines, n - 1)
            if not MAX_TOK.search(window):
                add("WARN", "no-max-tokens", "LLM call without max tokens: unbounded cost and latency")
            if not TIMEOUT.search(window) and not TIMEOUT.search(text[:3000]):
                add("WARN", "no-timeout", "LLM call without timeout/abort signal")
    if client_side and AI_CALL.search(text) and AI_IMPORT.search(text):
        findings.append(("ERROR", "ai-call-client", rel, 1, "Provider SDK called from a client component: move the call to a server route/action"))
    is_route = re.search(r"(^|/)(app/.*route\.(ts|js)|pages/api/|api/|routes?/|server/|actions?\.(ts|js))", rel)
    if is_route and AI_CALL.search(text) and not RATE.search(text) and not test:
        findings.append(("WARN", "ai-route-no-limit", rel, 1, "AI endpoint without visible rate limit/quota: add per-user limits (cost abuse)"))


def run(root):
    findings, models = [], collections.defaultdict(list)
    for rel in walk(root):
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
                scan(rel, f.read(), findings, models)
        except OSError:
            continue
    files_with_models = {r for locs in models.values() for r, _ in locs}
    if len(files_with_models) > 3:
        sample = ", ".join(sorted(models)[:5])
        findings.append(("WARN", "scattered-models", ".", 0, f"Model IDs hard-coded in {len(files_with_models)} files ({sample}): centralize in one config"))
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "ai_check")


if __name__ == "__main__":
    sys.exit(main())
