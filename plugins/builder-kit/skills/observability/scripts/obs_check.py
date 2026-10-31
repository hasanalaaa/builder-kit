#!/usr/bin/env python3
"""obs_check: does this app have the observability basics?

Usage: obs_check.py [root]
Checks: error-tracking SDK, structured logger, console/print in server code, secrets in log calls,
request-ID propagation, health endpoint, Web Vitals reporting, analytics without consent handling.
Each finding: LEVEL rule where  message. Exit 1 on any ERROR.
Silence a line with "obs-check: ignore".
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

CODE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py")
IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "__pycache__", ".turbo", ".expo"}
TEST = re.compile(r"(\.test\.|\.spec\.|__tests__|/tests?/|test_\w+\.py$|scripts?/|seed|mocks?/|fixtures?/|e2e/)")
SERVER = re.compile(r"(^|/)(app/api/|pages/api/|server/|api/|routes?/|actions?/|workers?/|jobs?/|lib/server|services?/)|(server|worker|main|app|manage)\.(ts|js|py)$|route\.(ts|js)$|actions?\.(ts|js)$")
TRACKERS = ("@sentry/", "sentry_sdk", "sentry-sdk", "@bugsnag/", "bugsnag", "rollbar", "@highlight-run/", "@datadog/browser-rum", "dd-trace",
            "newrelic", "@honeybadger-io/", "posthog-node", "@opentelemetry/", "crashlytics", "elastic-apm")
LOGGERS = ("pino", "winston", "bunyan", "consola", "@logtape/", "loglevel", "structlog", "loguru", "logging.config", "python-json-logger", "tslog")
LOG_CALL = re.compile(r"(?:console\.\w+|\blog(?:ger)?\.\w+|\bprint|logging\.\w+)\((.*)")
SENSITIVE = re.compile(r"(password|passwd|secret|token|api_?key|authorization|cookie|card_?number|cvv)", re.I)
STRING_TEXT = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`")


def logs_secret(line):
    """True when a log call passes a sensitive-looking variable; words inside string text don't count."""
    m = LOG_CALL.search(line)
    if not m:
        return False
    keep_interp = lambda s: " ".join(re.findall(r"\$\{([^}]*)\}", s.group(0))) if s.group(0).startswith("`") else ""
    return bool(SENSITIVE.search(STRING_TEXT.sub(keep_interp, m.group(1))))
CONSOLE = re.compile(r"\bconsole\.(log|info|debug)\(")
PRINT = re.compile(r"^\s*print\(")
REQ_ID = re.compile(r"x-request-id|requestId|request_id|correlation[-_]?id|traceparent|AsyncLocalStorage|contextvars", re.I)
ANALYTICS = re.compile(r"gtag\(|googletagmanager|fbq\(|connect\.facebook\.net|hotjar|clarity\.ms|posthog\.init|mixpanel\.init|amplitude\.init|segment\.com/analytics|_linkedin_partner_id|snap\.licdn|tiktok", re.I)
CONSENT = re.compile(r"consent|cookiebot|onetrust|klaro|cookieyes|iubenda|osano|termly|usercentrics|cookie-?banner|opt_out_capturing|optOut", re.I)


def walk(root):
    return bk.walk(root, None, IGNORE_DIRS)


read = bk.read


def deps_text(root, files):
    text = ""
    for f in ("package.json", "requirements.txt", "pyproject.toml", "Pipfile", "app.json", "app.config.ts", "app.config.js"):
        if f in files:
            text += read(root, f)
    return text


def run(root):
    files = walk(root)
    code = {f: read(root, f) for f in files if f.endswith(CODE)}
    deps = deps_text(root, files)
    all_code = "\n".join(code.values())
    findings = []
    has_server = any(SERVER.search(f) for f in code)
    if not any(t in deps or t in all_code for t in TRACKERS):
        findings.append(("ERROR", "no-error-tracking", ".", "No error-tracking SDK (Sentry or equivalent): production errors will be invisible"))
    if has_server and not any(re.search(rf"['\"]?{re.escape(l)}['\"]?", deps + all_code) for l in LOGGERS):
        findings.append(("WARN", "no-structured-logger", ".", "No structured logger (pino/winston/structlog/loguru)"))
    console_hits = 0
    for rel, text in code.items():
        server_file = bool(SERVER.search(rel)) and not TEST.search(rel)
        for n, line in enumerate(text.splitlines(), 1):
            if "obs-check: ignore" in line:
                continue
            if logs_secret(line) and not TEST.search(rel):
                findings.append(("ERROR", "secret-in-log", f"{rel}:{n}", "Log call mentions a secret/token/password: redact or remove"))
            if server_file and (CONSOLE.search(line) or (rel.endswith(".py") and PRINT.search(line))):
                console_hits += 1
                if console_hits <= 10:
                    findings.append(("WARN", "console-in-server", f"{rel}:{n}", "console.log/print in server code: use the structured logger"))
    if has_server and not REQ_ID.search(all_code):
        findings.append(("WARN", "no-request-id", ".", "No request/correlation ID handling found"))
    if has_server and not any(re.search(r"health|healthz|readyz|status", f, re.I) for f in files) \
            and not re.search(r"['\"]/(api/)?(health|healthz)['\"]", all_code):
        findings.append(("WARN", "no-health-endpoint", ".", "No health endpoint for uptime checks"))
    is_web = any(f.endswith((".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html")) for f in files)
    if is_web and not re.search(r"web-vitals|@vercel/speed-insights|useReportWebVitals|reportWebVitals|SpeedInsights|browserTracingIntegration", deps + all_code):
        findings.append(("WARN", "no-web-vitals", ".", "No real-user Web Vitals reporting"))
    web_text = all_code + "\n".join(read(root, f) for f in files if f.endswith((".html", ".astro", ".vue", ".svelte")))
    if ANALYTICS.search(web_text) and not CONSENT.search(web_text + deps):
        findings.append(("WARN", "analytics-no-consent", ".", "Analytics/ads scripts without visible consent handling (legal-compliance)"))
    try:
        mobile = "expo" in json.loads(read(root, "package.json") or "{}").get("dependencies", {})
    except json.JSONDecodeError:
        mobile = False
    if mobile and not re.search(r"@sentry/react-native|sentry-expo|crashlytics|@bugsnag/expo|@bugsnag/react-native", deps):
        findings.append(("ERROR", "no-crash-reporting", "package.json", "Mobile app without crash reporting"))
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "obs_check")


if __name__ == "__main__":
    sys.exit(main())
