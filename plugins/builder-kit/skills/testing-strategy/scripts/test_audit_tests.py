#!/usr/bin/env python3
"""Self-test for test_audit. Run: python3 test_audit_tests.py"""
# test-audit: ignore-file
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_tests  # noqa: E402


def run_on(files, modules=None):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in audit_tests.run(d, modules)[0]}


if __name__ == "__main__":
    assert {"no-tests", "no-test-script"} <= run_on({"src/features/billing/index.ts": "export const x = 1\n"})
    assert "no-test-script" not in run_on({"Makefile": "test:\n\tpython3 test_a.py\n", "test_a.py": "assert 1 + 1 == 2\n"})
    bad = {
        "package.json": '{"scripts": {"test": "vitest"}}',
        "src/features/billing/index.ts": "export const x = 1\n",
        "src/features/invites/index.ts": "export const y = 1\n",
        "src/features/billing/billing.test.ts": ("it.only('charges', () => { expect(true).toBe(true) })\n"
                                                 "it.skip('refunds', () => {})\n"
                                                 "test('waits', async () => { await page.waitForTimeout(2000) })\n"),
    }
    want = {"focused-test", "skipped-test", "sleep-in-test", "trivial-assert", "no-assertion", "untested-module"}
    got = run_on(bad)
    assert want <= got, sorted(want - got)
    good = {
        "package.json": '{"scripts": {"test": "vitest"}}',
        "src/features/billing/index.ts": "export const x = 1\n",
        "src/features/billing/billing.test.ts": "it('charges the card', async () => { expect(await charge()).toEqual({ ok: true }) })\n",
        "tests/test_api.py": "def test_health(client):\n    assert client.get('/health').status_code == 200\n",
    }
    got = run_on(good)
    assert not got, sorted(got)
    print("selftest OK")
