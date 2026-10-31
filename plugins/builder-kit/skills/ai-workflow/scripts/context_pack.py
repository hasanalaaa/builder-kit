#!/usr/bin/env python3
"""context_pack: print the facts an AI agent needs about a repo, as a draft CLAUDE.md "Per-project facts" block.

Usage: context_pack.py [root]
Prints to stdout only. Review and correct before saving it as CLAUDE.md / AGENTS.md.
"""
import argparse
import json
import os
import re
import sys

IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "__pycache__",
               ".turbo", ".expo", "Pods", ".dart_tool", ".idea", ".vscode", ".cache"}
JS_FRAMEWORKS = [("next", "Next.js"), ("astro", "Astro"), ("@remix-run/react", "Remix"), ("nuxt", "Nuxt"), ("@sveltejs/kit", "SvelteKit"),
                 ("expo", "Expo / React Native"), ("react-native", "React Native"), ("vite", "Vite"), ("react", "React"), ("vue", "Vue"),
                 ("svelte", "Svelte"), ("@nestjs/core", "NestJS"), ("hono", "Hono"), ("fastify", "Fastify"), ("express", "Express"),
                 ("electron", "Electron"), ("@tauri-apps/api", "Tauri"), ("wxt", "WXT extension")]
JS_TOOLS = [("typescript", "TypeScript"), ("tailwindcss", "Tailwind CSS"), ("@supabase/supabase-js", "Supabase"), ("prisma", "Prisma"),
            ("drizzle-orm", "Drizzle"), ("stripe", "Stripe"), ("@tanstack/react-query", "TanStack Query"), ("zod", "Zod"),
            ("next-intl", "next-intl"), ("i18next", "i18next"), ("@sentry/nextjs", "Sentry"), ("@sentry/react-native", "Sentry"),
            ("vitest", "Vitest"), ("jest", "Jest"), ("@playwright/test", "Playwright"), ("ai", "Vercel AI SDK"),
            ("@anthropic-ai/sdk", "Anthropic SDK"), ("openai", "OpenAI SDK"), ("firebase", "Firebase")]
PY_FRAMEWORKS = [("fastapi", "FastAPI"), ("django", "Django"), ("flask", "Flask"), ("sqlalchemy", "SQLAlchemy"), ("pydantic", "pydantic"),
                 ("pytest", "pytest"), ("alembic", "Alembic"), ("celery", "Celery")]
SCRIPT_KEYS = ["dev", "start", "build", "test", "test:e2e", "e2e", "lint", "typecheck", "type-check", "format", "db:migrate", "migrate", "db:types"]


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def package_manager(root):
    for lock, pm in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun"), ("package-lock.json", "npm")):
        if os.path.exists(os.path.join(root, lock)):
            return pm
    return "npm"


def top_dirs(root):
    out = []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if os.path.isdir(p) and name not in IGNORE_DIRS and not name.startswith("."):
            count = sum(len(fs) for d, ds, fs in os.walk(p) if not set(os.path.relpath(d, root).split(os.sep)) & IGNORE_DIRS)
            out.append((name, count))
    return out


def detect(root):
    facts = {"stack": [], "commands": [], "env": [], "docs": [], "entry": [], "contracts": []}
    pkg_text = read(root, "package.json")
    if pkg_text:
        try:
            pkg = json.loads(pkg_text)
        except json.JSONDecodeError:
            pkg = {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        facts["stack"] += [f"{label} {deps[k]}".strip() for k, label in JS_FRAMEWORKS + JS_TOOLS if k in deps]
        pm = package_manager(root)
        run = "npm run" if pm == "npm" else pm
        scripts = pkg.get("scripts", {})
        facts["commands"].append(f"Install: {pm} install")
        facts["commands"] += [f"{k}: {run} {k}" for k in SCRIPT_KEYS if k in scripts]
        if pkg.get("engines", {}).get("node") or os.path.exists(os.path.join(root, ".nvmrc")):
            facts["stack"].append("Node " + (pkg.get("engines", {}).get("node") or read(root, ".nvmrc").strip()))
    py = read(root, "pyproject.toml") + read(root, "requirements.txt")
    if py:
        facts["stack"] += [label for k, label in PY_FRAMEWORKS if re.search(rf"\b{k}\b", py, re.I)]
        if os.path.exists(os.path.join(root, "uv.lock")):
            facts["commands"].append("Install: uv sync · Test: uv run pytest")
        elif "[tool.poetry" in py:
            facts["commands"].append("Install: poetry install · Test: poetry run pytest")
        else:
            facts["commands"].append("Install: pip install -r requirements.txt · Test: pytest")
    for f, label in (("go.mod", "Go"), ("Cargo.toml", "Rust"), ("pubspec.yaml", "Flutter/Dart"), ("Package.swift", "Swift package"),
                     ("supabase/config.toml", "Supabase local"), ("docker-compose.yml", "Docker Compose"), ("Dockerfile", "Docker")):
        if os.path.exists(os.path.join(root, f)):
            facts["stack"].append(label)
    for f in (".env.example", ".env.sample", ".env.template"):
        facts["env"] += re.findall(r"^\s*([A-Z][A-Z0-9_]+)\s*=", read(root, f), re.M)
    for f in ("README.md", "SPEC.md", "ARCHITECTURE.md", "DESIGN.md", "CLAUDE.md", "AGENTS.md", "SECURITY_MAP.md", "docs/adr", "CHANGELOG.md"):
        if os.path.exists(os.path.join(root, f)):
            facts["docs"].append(f)
    for f in ("app/layout.tsx", "src/app/layout.tsx", "src/main.tsx", "src/main.ts", "src/index.ts", "main.py", "app/main.py",
              "manage.py", "server.ts", "src/server.ts", "app/_layout.tsx", "lib/main.dart", "cmd"):
        if os.path.exists(os.path.join(root, f)):
            facts["entry"].append(f)
    for pattern, label in ((r"app/api/v\d", "versioned API routes"), (r"supabase/migrations", "Supabase schema (migrations)"),
                           (r"prisma/schema.prisma", "Prisma schema"), (r"openapi\.(ya?ml|json)", "OpenAPI spec")):
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in IGNORE_DIRS]
            rel = os.path.relpath(d, root)
            if re.search(pattern, rel) or any(re.search(pattern, os.path.join(rel, f)) for f in files):
                facts["contracts"].append(label)
                break
    return facts


def render(root, facts):
    lines = ["# Project facts (draft from context_pack.py: verify and correct)", ""]
    lines.append("- Stack: " + (" · ".join(dict.fromkeys(facts["stack"])) or "<fill in>"))
    lines.append("- Commands: " + (" · ".join(facts["commands"]) or "<install / run / test / lint / typecheck / build>"))
    lines.append("- Entry points: " + (", ".join(facts["entry"]) or "<fill in>"))
    dirs = top_dirs(root)
    if dirs:
        lines.append("- Key directories: " + ", ".join(f"{n}/ ({c} files)" for n, c in dirs[:12]))
    lines.append("- Env vars (names only): " + (", ".join(facts["env"]) or "<none documented: add .env.example>"))
    lines.append("- Published contracts (global CLAUDE.md §4): " + (", ".join(dict.fromkeys(facts["contracts"])) or "<APIs, schemas, formats others depend on>"))
    lines.append("- Docs: " + (", ".join(facts["docs"]) or "<none yet: SPEC.md, ARCHITECTURE.md, DESIGN.md recommended>"))
    lines.append("- Known traps: <things that look wrong but are intentional>")
    lines.append("- Never touch: <applied migrations, generated files, vendored code, .env*>")
    lines.append("- Standards: builder-kit skills; run ship-check before merge")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    print(render(a.root, detect(a.root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
