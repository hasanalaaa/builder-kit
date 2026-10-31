#!/usr/bin/env python3
"""Self-test for perf_budget. Run: python3 test_perf_budget.py"""
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perf_budget  # noqa: E402


def write(d, rel, data):
    path = os.path.join(d, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def rules(d, *argv):
    a = perf_budget.parser().parse_args([d, *argv])
    return {f[1] for f in perf_budget.run(d, a)[0]}


if __name__ == "__main__":
    rnd = random.Random(1)
    noise = lambda n: bytes(rnd.getrandbits(8) for _ in range(n))
    with tempfile.TemporaryDirectory() as d:
        write(d, "package.json", b'{"dependencies": {"moment": "x", "antd": "x", "@mui/material": "x", "recharts": "x", "echarts": "x"}}')
        write(d, "dist/assets/app.js", noise(400_000))
        write(d, "dist/assets/app.css", noise(80_000))
        write(d, "public/hero.png", noise(600_000))
        write(d, "public/fonts/a.ttf", noise(200_000))
        got = rules(d, "--js-budget", "100", "--css-budget", "20")
        want = {"js-budget", "css-budget", "large-chunk", "heavy-dependency", "duplicate-ui-kits", "duplicate-chart-libs",
                "large-image", "font-format", "large-font"}
        assert want <= got, sorted(want - got)
    with tempfile.TemporaryDirectory() as d:
        write(d, "package.json", b'{"dependencies": {"next": "x", "date-fns": "x"}}')
        write(d, ".next/static/chunks/main.js", b"console.log(1);" * 2000)
        write(d, "public/hero.avif", noise(40_000))
        write(d, "public/fonts/a.woff2", noise(40_000))
        got = rules(d)
        assert not got, sorted(got)
    print("selftest OK")
