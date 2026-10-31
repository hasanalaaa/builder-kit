#!/usr/bin/env python3
"""release_check: is this repo ready to deploy safely?

Usage: release_check.py [root]
Checks: CI config and its steps, env vars used in code vs .env.example, committed .env files, lockfiles,
runtime version pinning, Dockerfile hygiene, health endpoint, migrations step.
Each finding: LEVEL rule where  message. Exit 1 on any ERROR.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "__pycache__", ".turbo", ".expo"}
CODE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".vue", ".svelte", ".astro")
ENV_USE = re.compile(r"process\.env\.([A-Z][A-Z0-9_]+)|process\.env\[['\"]([A-Z][A-Z0-9_]+)['\"]\]|import\.meta\.env\.([A-Z][A-Z0-9_]+)"
                     r"|os\.environ(?:\.get)?\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]|os\.environ\[['\"]([A-Z][A-Z0-9_]+)['\"]\]|os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]"
                     r"|Deno\.env\.get\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]")
BUILTIN_ENV = {"NODE_ENV", "CI", "PORT", "HOSTNAME", "VERCEL", "VERCEL_ENV", "VERCEL_URL", "NEXT_RUNTIME", "MODE", "DEV", "PROD", "SSR",
               "BASE_URL", "TZ", "HOME", "PATH", "PWD", "DEBUG", "NEXT_PHASE", "VERCEL_GIT_COMMIT_SHA", "GITHUB_ACTIONS", "RENDER", "FLY_APP_NAME"}
LOCKS = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock"]


def files_of(root):
    return bk.walk(root, None, IGNORE_DIRS, dot_dirs=True)


def tracked(root):
    try:
        out = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True, timeout=30)
        return set(out.stdout.splitlines()) if out.returncode == 0 else set()
    except (OSError, subprocess.SubprocessError):
        return set()


read = bk.read


def ci_checks(root, files, findings):
    ci = [f for f in files if re.match(r"\.github/workflows/.+\.ya?ml$", f) or f in (".gitlab-ci.yml", "bitbucket-pipelines.yml", ".circleci/config.yml")]
    if not ci:
        findings.append(("ERROR", "no-ci", ".", "No CI pipeline (.github/workflows/*.yml): add lint, typecheck, test, build on every push"))
        return
    text = "\n".join(read(root, f) for f in ci).lower()
    for step, pattern in (("lint", r"\blint\b|ruff|eslint|biome"), ("typecheck", r"typecheck|tsc\b|mypy|pyright|type-check|astro check"),
                          ("test", r"\btest\b|pytest|vitest|jest|playwright"), ("build", r"\bbuild\b")):
        if not re.search(pattern, text):
            findings.append(("WARN", f"ci-no-{step}", ci[0], f"CI does not appear to run {step}"))
    if re.search(r"uses:\s*[\w-]+/[\w-]+@(main|master|v\d+)\s*$", text, re.M):
        findings.append(("WARN", "ci-unpinned-actions", ci[0], "Actions pinned by tag/branch: pin by commit SHA (supply chain)"))
    if "permissions:" not in text:
        findings.append(("WARN", "ci-permissions", ci[0], "No explicit permissions: set least-privilege `permissions:`"))


def env_checks(root, files, findings):
    used = {}
    for rel in files:
        if rel.endswith(CODE) and not re.search(r"(\.test\.|\.spec\.|__tests__|/tests?/|(^|/)test_\w+\.py$)", rel):
            for m in ENV_USE.finditer(read(root, rel)):
                name = next(g for g in m.groups() if g)
                used.setdefault(name, rel)
    used = {k: v for k, v in used.items() if k not in BUILTIN_ENV}
    examples = [f for f in files if re.search(r"(^|/)\.env\.(example|sample|template)$|(^|/)example\.env$", f)]
    documented = set()
    for f in examples:
        documented |= set(re.findall(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]+)\s*=", read(root, f), re.M))
    missing = sorted(set(used) - documented - set(re.findall(r"\b[A-Z][A-Z0-9_]{3,}\b", read(root, "README.md"))))
    if missing and not examples:
        findings.append(("ERROR", "no-env-example", ".", f"Code reads {len(missing)} undocumented env vars and there is no .env.example"))
    elif missing:
        findings.append(("WARN", "env-undocumented", examples[0], f"Env vars used but not in {examples[0]}: {', '.join(missing[:12])}"
                         + (f" (+{len(missing) - 12})" if len(missing) > 12 else "")))
    committed = [f for f in tracked(root) if re.search(r"(^|/)\.env(\.[\w-]+)?$", f) and not re.search(r"\.(example|sample|template)$", f)]
    for f in committed:
        findings.append(("ERROR", "env-committed", f, "Real .env file committed to git: remove, rotate its secrets (launch-security 24/25)"))


def runtime_checks(root, files, findings):
    has_pkg = "package.json" in files
    if has_pkg:
        locks = [l for l in LOCKS if l in files]
        if not locks:
            findings.append(("ERROR", "no-lockfile", ".", "No lockfile: installs are not reproducible"))
        elif len(locks) > 1:
            findings.append(("WARN", "multiple-lockfiles", ".", f"Several lockfiles ({', '.join(locks)}): pick one package manager"))
        try:
            pkg = json.loads(read(root, "package.json") or "{}")
        except json.JSONDecodeError:
            pkg = {}
        if not (pkg.get("engines", {}).get("node") or ".nvmrc" in files or ".node-version" in files or ".tool-versions" in files):
            findings.append(("WARN", "node-unpinned", "package.json", "Node version not pinned (.nvmrc or engines.node)"))
        if "build" not in pkg.get("scripts", {}):
            findings.append(("WARN", "no-build-script", "package.json", "No build script"))
    is_py = any(f in files for f in ("pyproject.toml", "requirements.txt", "Pipfile"))
    if is_py and not any(f in files for f in ("uv.lock", "poetry.lock", "Pipfile.lock", "requirements.lock")) \
            and not re.search(r"==", read(root, "requirements.txt")):
        findings.append(("WARN", "py-unpinned", ".", "Python dependencies not locked (uv.lock / poetry.lock / pinned requirements)"))
    if is_py and not any(f in files for f in (".python-version", ".tool-versions", "runtime.txt")) and "requires-python" not in read(root, "pyproject.toml"):
        findings.append(("WARN", "python-unpinned", ".", "Python version not pinned"))


def docker_checks(root, files, findings):
    for rel in [f for f in files if os.path.basename(f) == "Dockerfile" or f.endswith(".Dockerfile")]:
        text = read(root, rel)
        if re.search(r"^FROM\s+\S+:latest\b|^FROM\s+[^:\s@]+\s*(AS|$)", text, re.M | re.I):
            findings.append(("WARN", "docker-unpinned-base", rel, "Base image not pinned (avoid :latest / no tag)"))
        if not re.search(r"^USER\s+(?!root)\S+", text, re.M):
            findings.append(("WARN", "docker-root", rel, "Container runs as root: add a non-root USER"))
        if "HEALTHCHECK" not in text and "fly.toml" not in files:
            findings.append(("WARN", "docker-no-healthcheck", rel, "No HEALTHCHECK"))
        if re.search(r"^(ENV|ARG)\s+\w*(SECRET|TOKEN|PASSWORD|API_KEY)\w*\s*=?\s*\S+", text, re.M | re.I):
            findings.append(("ERROR", "docker-secret", rel, "Secret baked into the image via ENV/ARG"))
        if ".dockerignore" not in files:
            findings.append(("WARN", "no-dockerignore", rel, "No .dockerignore: .git/.env/node_modules may be copied into the image"))


def app_checks(root, files, findings):
    is_server = any(re.search(r"(^|/)(app/api/|pages/api/|server\.(ts|js|py)$|main\.py$|app\.py$|manage\.py$|routes?/)", f) for f in files)
    if is_server and not any(re.search(r"health|healthz|readyz|livez|status", f, re.I) for f in files) \
            and not any(re.search(r"['\"]/(api/)?(health|healthz|status)['\"]", read(root, f)) for f in files if f.endswith(CODE)):
        findings.append(("WARN", "no-health-endpoint", ".", "No health endpoint (/api/health returning status + version)"))
    has_migrations = any(re.search(r"(^|/)(migrations?|supabase/migrations|prisma/migrations|drizzle|alembic)/", f) for f in files)
    if has_migrations:
        ci_text = "\n".join(read(root, f) for f in files if f.startswith(".github/workflows/"))
        deploy_cfg = "\n".join(read(root, f) for f in ("package.json", "fly.toml", "render.yaml", "railway.json", "Procfile", "vercel.json") if f in files)
        if not re.search(r"migrate|db push|alembic upgrade|migration up", ci_text + deploy_cfg, re.I):
            findings.append(("WARN", "migrations-manual", ".", "Migrations exist but no pipeline/deploy step runs them"))


def run(root):
    files = files_of(root)
    findings = []
    ci_checks(root, files, findings)
    env_checks(root, files, findings)
    runtime_checks(root, files, findings)
    docker_checks(root, files, findings)
    app_checks(root, files, findings)
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "release_check", a.root)


if __name__ == "__main__":
    sys.exit(main())
