#!/usr/bin/env python3
"""Self-test for a11y_lint. Run: python3 test_a11y_lint.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_lint  # noqa: E402

BAD = """<html>
<img src="/logo.png">
<input type="email" placeholder="Email">
<div onClick={open}>Open</div>
<a onClick={go}>Go</a>
<a href="#">Top</a>
<span tabIndex={3}>x</span>
<input autoFocus aria-label="q" />
<iframe src="/map"></iframe>
<button aria-hidden="true">x</button>
<video src="/v.mp4" autoPlay></video>
<button onClick={close}><XIcon /></button>
<h1>Title</h1>
<h3>Skipped</h3>
<Pressable onPress={go}><Text>Go</Text></Pressable>
</html>
"""
GOOD = """<html lang="ar" dir="rtl">
<img src="/logo.png" alt="Rawdah" />
<label htmlFor="email">Email</label>
<input id="email" type="email" autoComplete="email" />
<label>Name <input name="name" /></label>
<button onClick={open}>Open</button>
<a href="/go">Go</a>
<iframe src="/map" title="Store location map"></iframe>
<video src="/v.mp4" autoPlay muted controls></video>
<button onClick={close} aria-label="Close"><XIcon /></button>
<h1>Title</h1>
<h2>Section</h2>
<Pressable onPress={go} accessibilityRole="button" accessibilityLabel="Go"><Text>Go</Text></Pressable>
</html>
"""


def run_on(body):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "page.tsx"), "w", encoding="utf-8") as f:
            f.write(body)
        return {f[1] for f in a11y_lint.run(d)}


if __name__ == "__main__":
    got = run_on(BAD)
    want = {"html-lang", "img-alt", "input-label", "click-non-interactive", "anchor-no-href", "anchor-hash",
            "positive-tabindex", "autofocus", "iframe-title", "aria-hidden-focusable", "autoplay-media",
            "icon-button-name", "heading-skip", "rn-touchable-label"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD)
    assert not got, sorted(got)
    print("selftest OK")
