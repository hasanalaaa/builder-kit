#!/usr/bin/env python3
"""Self-test for bk_add. Run: python3 test_bk_add.py"""
import contextlib
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bk_add  # noqa: E402

EXPECTED = {"ai-chat-stream", "file-upload", "owner-scoped-api", "postgres-rls", "stripe-webhook"}


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = bk_add.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def files_in(root):
    return sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs)


if __name__ == "__main__":
    # Every recipe.json is valid, its sources exist, and each ships at least one test and an ADAPT list.
    assert set(bk_add.names()) == EXPECTED, bk_add.names()
    for name in bk_add.names():
        r = bk_add.load(name)
        assert all(os.path.isfile(e["src"]) for e in r["files"]), name
        assert any(e["to"].endswith(".test.ts") for e in r["files"]), name
        assert r["adapt"] and r["summary"], name
        assert len({e["to"] for e in r["files"]}) == len(r["files"]), f"{name}: duplicate destination"

    code, out, _ = run("--list")
    assert code == 0 and all(n in out for n in EXPECTED), out

    code, _, err = run("nope")
    assert code == 2 and "unknown recipe 'nope'" in err, err

    with tempfile.TemporaryDirectory() as d:
        code, out, _ = run("stripe-webhook", "--dest", d, "--dry-run")
        assert code == 0 and "would add" in out and files_in(d) == [], (out, files_in(d))

        code, out, _ = run("stripe-webhook", "--dest", d)
        assert code == 0, out
        assert "src/app/api/webhooks/stripe/route.ts" in files_in(d), files_in(d)
        assert "npm i stripe pg" in out and "STRIPE_WEBHOOK_SECRET" in out and "ADAPT" in out and "npx vitest run" in out, out

        # A second recipe shares src/lib/env.ts etc.: identical files are skipped, not conflicts.
        code, out, _ = run("owner-scoped-api", "--dest", d)
        assert code == 0 and "same, skipped" in out and "src/lib/env.ts" in out, out

        # A different existing file is a conflict: exit 1, nothing at all is copied.
        with open(os.path.join(d, "src/lib/db.ts"), "w") as f:
            f.write("// mine\n")
        before = files_in(d)
        code, _, err = run("postgres-rls", "--dest", d)
        assert code == 1 and "conflict: src/lib/db.ts" in err, err
        assert files_in(d) == before
        with open(os.path.join(d, "src/lib/db.ts")) as f:
            assert f.read() == "// mine\n"

        # An optional file the project already has is kept.
        with open(os.path.join(d, "vitest.config.mts"), "w") as f:
            f.write("export default {}\n")
        code, out, _ = run("file-upload", "--dest", d)
        assert code == 0 and "exists, kept yours" in out, out
        with open(os.path.join(d, "vitest.config.mts")) as f:
            assert f.read() == "export default {}\n"
    print("selftest OK")
