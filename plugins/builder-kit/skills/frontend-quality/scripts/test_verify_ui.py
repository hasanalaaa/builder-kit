#!/usr/bin/env python3
"""Self-test for verify_ui (offline, Python only: Node is faked). Run: python3 test_verify_ui.py"""
import contextlib
import io
import json
import os
import socket
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_ui  # noqa: E402

BASE = "http://localhost:3000"
PAGE = {"route": "/", "console": [], "pageErrors": [], "requests": [], "navError": None, "overflow": None,
        "lang": "en", "dir": "", "imgNoAlt": [], "imgBroken": [], "axe": []}
BAD = {"pages": [
    {**PAGE, "viewport": 375, "console": ["boom " + "x" * 300, "Failed to load resource: 404"], "pageErrors": ["TypeError: a is undefined"],
     "requests": [{"url": BASE + "/api/missing?q=1", "method": "GET", "status": 404},
                  {"url": "https://cdn.example.com/x.js", "method": "GET", "failure": "net::ERR_NAME_NOT_RESOLVED"},
                  {"url": BASE + "/_next/prefetch", "method": "GET", "failure": "net::ERR_ABORTED"}],
     "overflow": {"width": 600, "el": "div.box"}, "lang": "ar", "imgNoAlt": ["/logo.png"], "imgBroken": ["/gone.png"],
     "axe": [{"id": "color-contrast", "impact": "serious", "help": "Contrast", "nodes": 3, "target": "p"},
             {"id": "region", "impact": "moderate", "help": "Landmarks", "nodes": 1, "target": "div"}]},
    {**PAGE, "viewport": 1280, "console": ["boom " + "x" * 300], "overflow": {"width": 1400, "el": ""}, "lang": "ar"},
    {**PAGE, "route": "/pricing", "viewport": 375, "navError": "net::ERR_CONNECTION_REFUSED"},
]}
CLEAN = {"pages": [{**PAGE, "viewport": 375, "lang": "ar", "dir": "rtl", "shot": "/s/index-375.png"},
                   {**PAGE, "viewport": 1280, "shot": "/s/index-1280.png"}]}


def static_server(port):
    """Shell command serving the cwd. Plain TCPServer, not `python -m http.server`: HTTPServer.server_bind calls
    socket.getfqdn(), which can hang 20s+ on macOS CI runners."""
    code = (f"import http.server as h, socketserver as s; s.TCPServer.allow_reuse_address = True; "
            f"s.TCPServer(('127.0.0.1', {port}), h.SimpleHTTPRequestHandler).serve_forever()")
    return f'{sys.executable} -c "{code}"'


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fake_node(d, payload, code):
    """A `node` on PATH that prints payload: the Python half is tested without a browser."""
    path = os.path.join(d, "node")
    with open(path, "w") as f:
        f.write(f"#!{sys.executable}\nimport sys\nsys.stdin.read()\nprint({json.dumps(json.dumps(payload))})\nsys.exit({code})\n")
    os.chmod(path, 0o755)


def run_main(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = verify_ui.main(argv)
    return code, buf.getvalue()


def test_findings():
    got = verify_ui.findings_from(BAD, BASE)
    rules = [f[1] for f in got]
    assert sorted(set(rules)) == ["axe-color-contrast", "axe-region", "console-error", "img-alt", "img-broken", "overflow-mobile",
                                  "page-error", "page-load", "request-failed", "rtl-dir"], rules
    assert rules.count("console-error") == 1, "same console error at both viewports is reported once"
    assert rules.count("overflow-mobile") == 1, "overflow only counts at 375"
    assert rules.count("request-failed") == 1, "third-party and aborted requests are skipped by default"
    by = {f[1]: f for f in got}
    assert by["request-failed"][4] == "404 GET /api/missing?q=1", by["request-failed"]
    assert len(by["console-error"][4]) == verify_ui.MAX_MSG and by["console-error"][4].endswith("...")
    assert by["axe-color-contrast"][0] == "ERROR" and by["axe-region"][0] == "WARN"
    assert by["page-load"][2] == "/pricing" and all(f[3] == 0 for f in got)
    assert "600px" in by["overflow-mobile"][4] and "div.box" in by["overflow-mobile"][4]
    assert any("cdn.example.com" in f[4] for f in verify_ui.findings_from(BAD, BASE, all_origins=True))
    assert not verify_ui.findings_from(CLEAN, BASE)
    assert [f[1] for f in verify_ui.findings_from(CLEAN, BASE, rtl=True)] == ["rtl-dir"], "--rtl checks pages without an RTL lang too"


def test_args():
    a = verify_ui.parse_args([])
    assert (a.url, a.routes, a.start, a.rtl, a.all_origins) == (BASE, ["/"], None, False, False)
    a = verify_ui.parse_args(["--url", "http://127.0.0.1:5173/", "--routes", "/", "pricing", "/a/b/", "--rtl", "--start", "npm run dev"])
    assert a.url == "http://127.0.0.1:5173" and a.routes == ["/", "/pricing", "/a/b/"] and a.rtl and a.start == "npm run dev"
    here = verify_ui.default_out(os.path.dirname(os.path.abspath(__file__)))
    assert os.sep + ".git" in here and here.endswith(os.path.join("builder-kit", "shots")), "shots must stay out of the working tree"
    with tempfile.TemporaryDirectory() as d:
        assert verify_ui.default_out(d).startswith(tempfile.gettempdir()), "outside git: temp dir"
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            verify_ui.parse_args(["--url", "localhost:3000"])
            raise AssertionError("a URL without scheme must be rejected")
        except SystemExit as e:
            assert e.code == 2


def test_serve():
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    # `& wait` keeps the server a grandchild: only killing the process group stops it.
    cmd = f"{static_server(port)} >/dev/null 2>&1 & wait"
    with tempfile.TemporaryDirectory() as d:
        log = os.path.join(d, "server.log")
        with verify_ui.serve(cmd, url, 20, log):
            assert verify_ui.answers(url)
        assert not verify_ui.answers(url), "server still up after the block"
        try:
            with verify_ui.serve(cmd, url, 20, log):
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass  # raised on purpose to simulate Ctrl-C; the assert below checks the cleanup
        assert not verify_ui.answers(url), "server still up after Ctrl-C"
        for bad in ("exit 7", None):
            try:
                with verify_ui.serve(bad, url, 20, log):
                    raise AssertionError("block must not run without a server")
            except verify_ui.Unchecked as e:
                assert ("exited with 7" if bad else "nothing answers") in str(e), e


def test_main():
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    old_cwd, old_path = os.getcwd(), os.environ["PATH"]
    with tempfile.TemporaryDirectory() as d:
        bin_dir, shots = os.path.join(d, "bin"), os.path.join(d, "shots")
        os.makedirs(bin_dir)
        os.chdir(d)
        try:
            code, out = run_main(["--url", url, "--out", shots])
            assert code == 3 and verify_ui.INSTALL in out, out  # no Playwright in this project (with or without a real node)
            os.environ["PATH"] = bin_dir
            pkg = os.path.join(d, "node_modules", "@playwright", "test")
            os.makedirs(pkg)
            with open(os.path.join(pkg, "package.json"), "w") as f:
                f.write("{}")
            code, out = run_main(["--url", url, "--out", shots])
            assert code == 3 and "Node.js not found" in out, out
            start = static_server(port)
            fake_node(bin_dir, {"error": "browser", "message": "Executable doesn't exist at /x/chrome"}, 3)
            code, out = run_main(["--url", url, "--out", shots, "--start", start])
            assert code == 3 and "Executable doesn't exist" in out and verify_ui.INSTALL in out, out
            fake_node(bin_dir, BAD, 0)
            os.environ["BUILDER_KIT_FORMAT"] = "json"
            code, out = run_main(["--url", url, "--out", shots, "--start", start])
            rows = [json.loads(line) for line in out.splitlines() if line.startswith("{")]
            assert code == 1 and any(r["rule"] == "page-load" and r["path"] == "/pricing" for r in rows), out
            del os.environ["BUILDER_KIT_FORMAT"]
            fake_node(bin_dir, CLEAN, 0)
            code, out = run_main(["--url", url, "--out", shots, "--start", start])
            assert code == 0 and "/s/index-375.png" in out and "verify_ui: 0 ERROR" in out, out
            fake_node(bin_dir, {}, 1)
            code, out = run_main(["--url", url, "--out", shots, "--start", start])
            assert code == 2 and "browser run failed" in out, out
            assert not verify_ui.answers(url), "--start server left running"
        finally:
            os.chdir(old_cwd)
            os.environ["PATH"] = old_path
            os.environ.pop("BUILDER_KIT_FORMAT", None)


if __name__ == "__main__":
    test_findings()
    test_args()
    test_serve()
    test_main()
    print("selftest OK")
