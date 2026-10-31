#!/usr/bin/env python3
"""Self-test for error_scan. Run: python3 test_error_scan.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import error_scan  # noqa: E402

BAD = {
    "app/page.tsx": "export default function P(){ return null }\n",
    "src/api.ts": ("export async function load(){\n  try { await save() } catch (e) {}\n"
                   "  try { x() } catch (err) { console.error(err) }\n"
                   "  p.catch(() => {})\n  const r = await fetch('/x')\n  alert(err.message)\n"
                   "  try {\n    y()\n  } catch {\n  }\n}\n"),
    "svc/job.py": ("import requests, httpx\ntry:\n    run()\nexcept:\n    pass\n"
                   "try:\n    run()\nexcept ValueError: pass\nrequests.get(url)\nhttpx.get(url)\n"),
    "cmd/main.go": "func main() {\n\tif err != nil { }\n}\n",
    "ios/App.swift": "let d = try! Data(contentsOf: u)\n",
}
GOOD = {
    "app/page.tsx": "export default function P(){ return null }\n",
    "app/error.tsx": "'use client'\nexport default function E({ reset }){ return <button onClick={reset}>Try again</button> }\n",
    "src/api.ts": ("export async function load(){\n  const r = await fetch('/x', { signal: AbortSignal.timeout(5000) })\n"
                   "  if (!r.ok) throw new AppError('dependency_failed', 'Try again')\n"
                   "  try { await save() } catch (e) { throw new AppError('internal', 'Could not save', {}, { cause: e }) }\n}\n"),
    "svc/job.py": "import requests\ntry:\n    run()\nexcept ValueError as e:\n    raise AppError('bad') from e\nrequests.get(url, timeout=(3, 10))\n",
}


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in error_scan.run(d)}


if __name__ == "__main__":
    got = run_on(BAD)
    want = {"empty-catch", "except-pass", "except-pass-specific", "bare-except", "catch-log-only", "promise-catch-noop", "requests-no-timeout",
            "httpx-no-timeout", "go-ignored-error", "swift-try-bang", "alert-error-message", "fetch-unchecked",
            "fetch-no-timeout", "no-error-boundary"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD)
    assert not got, sorted(got)
    print("selftest OK")
