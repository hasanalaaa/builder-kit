#!/usr/bin/env python3
"""Self-test for rtl_lint. Run: python3 test_rtl_lint.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rtl_lint  # noqa: E402

BAD = {
    "package.json": '{"dependencies": {"next-intl": "x"}}',
    "app/layout.tsx": "export default function L({children}){ return <html lang=\"en\"><body>{children}</body></html> }\n",
    "app/page.tsx": ('export default function P(){ return <div className="ml-4 pr-2 text-left rounded-l-lg left-0">'
                     '<ChevronRight className="h-4 w-4" />Save changes</div> }\n'
                     "const d = new Date().toLocaleDateString()\n"),
    "styles/a.css": ".x { margin-left: 8px; text-align: right; float: left; left: 0 }\n",
    "mobile/Row.tsx": "const s = StyleSheet.create({ row: { marginLeft: 8, paddingRight: 4 } })\n",
    "lib/w.dart": "Padding(padding: EdgeInsets.only(left: 8), child: x)\n",
}
GOOD = {
    "package.json": '{"dependencies": {"next-intl": "x"}}',
    "app/[locale]/layout.tsx": "export default function L({children, locale, dir}){ return <html lang={locale} dir={dir}><body>{children}</body></html> }\n",
    "app/[locale]/page.tsx": ('export default function P(){ const t = useTranslations(); return <div className="ms-4 pe-2 text-start rounded-s-lg start-0">'
                              '<ChevronRight className="h-4 w-4 rtl:-scale-x-100" />{t("save")}</div> }\n'
                              "const d = new Intl.DateTimeFormat(locale, { dateStyle: 'long' }).format(now)\n"),
    "styles/a.css": ".x { margin-inline-start: 8px; text-align: start; inset-inline-start: 0 }\n.s { box-shadow: 2px 2px 4px #0003 }\n",
    "mobile/Row.tsx": "const s = StyleSheet.create({ row: { marginStart: 8, paddingEnd: 4 } })\n",
}


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in rtl_lint.run(d)}


if __name__ == "__main__":
    got = run_on(BAD)
    want = {"html-lang-dir", "physical-tailwind", "unflipped-icon", "hardcoded-string", "localeless-format",
            "physical-css", "physical-rn-style", "physical-flutter"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD)
    assert not got, sorted(got)
    print("selftest OK")
