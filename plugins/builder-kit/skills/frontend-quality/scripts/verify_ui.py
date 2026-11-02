#!/usr/bin/env python3
"""verify_ui: open the real pages in a browser and report only what is broken.

Usage (from the project root):
  verify_ui.py [--url http://localhost:3000] [--routes / /pricing ...] [--start "npm run dev"] [--out DIR] [--rtl] [--all-origins]
Each route at 375x812 and 1280x800: console errors, uncaught page errors, failed requests (same origin unless
--all-origins), horizontal overflow at 375, <img> without alt or broken, axe-core violations (when the project has
axe-core), and dir="rtl" when --rtl or <html lang> is Arabic/Hebrew/Persian/Urdu. Screenshots go to --out
(default <git-dir>/builder-kit/shots, outside the working tree) and are printed as paths.
Needs Playwright in the project: npm i -D @playwright/test && npx playwright install chromium (nothing is downloaded here).
Exit 0 clean, 1 on any ERROR, 2 when the app or the browser run could not be checked, 3 when Playwright/Node is missing.
"""
import argparse
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

NODE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_ui.mjs")
INSTALL = "npm i -D @playwright/test && npx playwright install chromium"
RTL_LANGS = {"ar", "he", "fa", "ur"}
MAX_MSG = 160
VIEWPORTS = 2


class Unchecked(Exception):
    """The pages could not be checked at all (no server, browser run crashed): exit 2, never a silent pass."""


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="http://localhost:3000", help="base URL of the running app")
    p.add_argument("--routes", nargs="+", default=["/"], help="paths to open (default /)")
    p.add_argument("--start", help='command that starts the dev server, e.g. "npm run dev" (killed at the end)')
    p.add_argument("--timeout", type=float, default=90, help="seconds to wait for --start to serve --url")
    p.add_argument("--out", help="screenshot folder (default <git-dir>/builder-kit/shots)")
    p.add_argument("--rtl", action="store_true", help='require dir="rtl" on every page')
    p.add_argument("--all-origins", action="store_true", help="also report failed third-party requests")
    a = p.parse_args(argv)
    if urllib.parse.urlsplit(a.url).scheme not in ("http", "https"):
        p.error(f"--url must be http(s)://..., got {a.url!r}")
    a.url = a.url.rstrip("/")
    a.routes = ["/" + r.lstrip("/") for r in a.routes]
    return a


def find_package(root, names):
    """First of `names` installed in node_modules at root or above (npm/pnpm/yarn hoisting) → (name, dir)."""
    d = os.path.abspath(root)
    while True:
        for n in names:
            pkg = os.path.join(d, "node_modules", n)
            if os.path.isfile(os.path.join(pkg, "package.json")):
                return n, pkg
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def default_out(root):
    try:
        p = subprocess.run(["git", "-C", root, "rev-parse", "--absolute-git-dir"], capture_output=True, text=True, timeout=10)
        if p.returncode == 0 and p.stdout.strip():
            return os.path.join(p.stdout.strip(), "builder-kit", "shots")
    except (OSError, subprocess.SubprocessError):
        pass  # not a git repo: fall back to the temp dir
    return os.path.join(tempfile.gettempdir(), "builder-kit-shots")


def answers(url):
    """True when anything HTTP answers at url (a 404 or 500 still means the server is up)."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never route localhost through a proxy
    try:
        opener.open(url, timeout=2).close()
        return True
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def wait_for(url, timeout, proc=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if answers(url):
            return True
        if proc is not None and proc.poll() is not None:
            return False
        time.sleep(0.3)
    return False


def group_alive(proc):
    proc.poll()  # reap the shell first: an unreaped zombie still counts as a group member
    try:
        os.killpg(proc.pid, 0)
        return True
    except (ProcessLookupError, PermissionError):  # macOS answers EPERM for a group left with only zombies
        return False


def stop(proc, grace=5):
    """Kill the whole process group: `npm run dev` leaves its node child running if only the shell dies."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, sig)
        deadline = time.monotonic() + grace
        while group_alive(proc) and time.monotonic() < deadline:
            time.sleep(0.1)
        if not group_alive(proc):
            return


@contextlib.contextmanager
def serve(cmd, url, timeout, log):
    """Run `cmd` until the block ends (also on errors and Ctrl-C); without cmd, require something at url."""
    if not cmd or answers(url):
        if cmd:
            print(f"verify_ui: {url} already answers, not starting {cmd!r}")
        elif not wait_for(url, 5):
            raise Unchecked(f"nothing answers at {url}: start the app or pass --start \"npm run dev\"")
        yield
        return
    with open(log, "w") as f:
        # bk-ignore: shell-true -- --start is the user's own dev-server command line, typed by them, run like `npm run dev`
        proc = subprocess.Popen(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        if not wait_for(url, timeout, proc):
            why = f"exited with {proc.returncode}" if proc.poll() is not None else f"no answer within {timeout:g}s"
            raise Unchecked(f"{cmd!r} did not serve {url} ({why}); log: {log}")
        yield
    finally:
        stop(proc)


def short(text):
    text = " ".join(str(text).split())
    return text if len(text) <= MAX_MSG else text[: MAX_MSG - 3] + "..."


def findings_from(result, base, rtl=False, all_origins=False):
    """The browser run's raw facts → bk finding tuples, one per (rule, route, message) across viewports."""
    origin = urllib.parse.urlsplit(base)[:2]
    found, seen = [], set()

    def add(level, rule, route, msg):
        msg = short(msg)
        if (rule, route, msg) not in seen:
            seen.add((rule, route, msg))
            found.append((level, rule, route, 0, msg))

    for p in result.get("pages", []):
        route = p["route"]
        if p.get("navError"):
            add("ERROR", "page-load", route, p["navError"])
            continue
        for text in p.get("console", []):
            # Chromium logs every failed resource as a console error; request-failed already reports it.
            if not text.startswith("Failed to load resource"):
                add("ERROR", "console-error", route, text)
        for text in p.get("pageErrors", []):
            add("ERROR", "page-error", route, text)
        for q in p.get("requests", []):
            u = urllib.parse.urlsplit(q["url"])
            same = u[:2] == origin
            # ERR_ABORTED is a navigation or prefetch the page itself cancelled, not a broken request.
            if (not same and not all_origins) or q.get("failure") == "net::ERR_ABORTED":
                continue
            where = (u.path + ("?" + u.query if u.query else "")) if same else q["url"]
            add("ERROR", "request-failed", route, f"{q.get('status') or q.get('failure')} {q.get('method', 'GET')} {where}")
        o = p.get("overflow")
        if o and p.get("viewport") == 375:
            add("ERROR", "overflow-mobile", route, f"page scrolls sideways at 375px: {o['width']}px wide" + (f", widest {o['el']}" if o.get("el") else ""))
        for src in p.get("imgNoAlt", []):
            add("ERROR", "img-alt", route, f"<img> without alt (alt=\"\" if decorative): {src}")
        for src in p.get("imgBroken", []):
            add("ERROR", "img-broken", route, f"image failed to load: {src}")
        for v in p.get("axe", []):
            level = "ERROR" if v.get("impact") in ("serious", "critical") else "WARN"
            add(level, f"axe-{v['id']}", route, f"{v.get('help', v['id'])} ({v.get('nodes', 1)}x, e.g. {v.get('target') or '?'})")
        lang = (p.get("lang") or "").lower().split("-")[0]
        if (rtl or lang in RTL_LANGS) and (p.get("dir") or "").lower() != "rtl":
            add("ERROR", "rtl-dir", route, 'dir="rtl" missing on <html>' + (f' (lang="{lang}")' if lang else ""))
    return found


def run_browser(node, cfg):
    timeout = 60 * VIEWPORTS * len(cfg["routes"]) + 30
    try:
        p = subprocess.run([node, NODE_SCRIPT], input=json.dumps(cfg), capture_output=True, text=True, timeout=timeout, cwd=cfg["root"])
    except subprocess.TimeoutExpired:
        raise Unchecked(f"browser run timed out after {timeout}s")
    last = (p.stdout.strip().splitlines() or [""])[-1]
    try:
        result = json.loads(last)
    except json.JSONDecodeError:
        result = None
    if p.returncode == 3 or (result or {}).get("error") == "browser":
        return None, (result or {}).get("message", "browser failed to launch")
    if p.returncode != 0 or not isinstance(result, dict):
        tail = "\n".join((p.stderr or p.stdout).strip().splitlines()[-6:])
        raise Unchecked(f"browser run failed (exit {p.returncode}):\n{tail}")
    return result, None


def main(argv=None):
    a = parse_args(argv)
    root = os.getcwd()
    node = shutil.which("node")
    pkg, _ = find_package(root, ("@playwright/test", "playwright"))
    if not node or not pkg:
        print(f"verify_ui: {'Playwright' if node else 'Node.js'} not found for {root}. Install: {INSTALL}")
        return 3
    _, axe_dir = find_package(root, ("axe-core",))
    axe = os.path.join(axe_dir, "axe.min.js") if axe_dir else None
    out = os.path.abspath(a.out or default_out(root))
    os.makedirs(out, exist_ok=True)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))  # turn `kill` into SystemExit so serve() still stops the server
    cfg = {"root": root, "pkg": pkg, "axe": axe if axe and os.path.isfile(axe) else None, "base": a.url, "routes": a.routes, "out": out}
    try:
        with serve(a.start, a.url, a.timeout, os.path.join(out, "server.log")):
            result, launch_error = run_browser(node, cfg)
    except Unchecked as e:
        print(f"verify_ui: {e}")
        return 2
    if launch_error:
        print(f"verify_ui: {launch_error}\nInstall: {INSTALL}")
        return 3
    shots = [p["shot"] for p in result.get("pages", []) if p.get("shot")]
    if shots:
        print("screenshots:\n" + "\n".join(f"  {s}" for s in shots))
    note = "" if cfg["axe"] else " · axe-core not installed (npm i -D axe-core for a11y checks)"
    return bk.report(findings_from(result, a.url, a.rtl, a.all_origins), "verify_ui", root, note=note)


if __name__ == "__main__":
    sys.exit(main())
