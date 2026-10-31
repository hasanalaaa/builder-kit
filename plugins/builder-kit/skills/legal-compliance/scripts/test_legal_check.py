#!/usr/bin/env python3
"""Self-test for legal_check. Run: python3 test_legal_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import legal_check  # noqa: E402

BAD = {
    "app/page.tsx": ("<link href=\"https://fonts.googleapis.com/css2?family=Cairo\" rel=\"stylesheet\"/>\n"
                     "<iframe src=\"https://www.youtube.com/embed/abc\"></iframe>\n"
                     "<script src=\"https://www.googletagmanager.com/gtag/js\"></script>\n"),
    "app/signup/page.tsx": "await supabase.auth.signUp({ email, password })\n",
}
GOOD = {
    "app/page.tsx": "<iframe src=\"https://www.youtube-nocookie.com/embed/abc\"></iframe>\n<ConsentBanner />\n<script src=\"https://www.googletagmanager.com/gtag/js\"></script>\n",
    "app/signup/page.tsx": "await supabase.auth.signUp({ email, password })\n",
    "app/privacy/page.tsx": "export default () => <h1>Privacy</h1>\n",
    "app/terms/page.tsx": "export default () => <h1>Terms</h1>\n",
    "app/settings/actions.ts": "export async function deleteAccount() {}\nexport async function exportMyData() {}\n",
}


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in legal_check.run(d)}


if __name__ == "__main__":
    got = run_on(BAD)
    want = {"no-privacy-policy", "no-terms", "no-account-deletion", "no-data-export", "trackers-no-consent", "google-fonts-cdn", "youtube-embed"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD)
    assert not got, sorted(got)
    print("selftest OK")
