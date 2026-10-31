#!/usr/bin/env python3
"""Self-test for fe_check. Run: python3 test_fe_check.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fe_check  # noqa: E402

BAD_PAGE = """'use client'
// @ts-ignore
export default function Page({ items }: { items: any }) {
  const [full, setFull] = useState('')
  useEffect(() => { setFull(first + last) }, [first, last])
  useEffect(() => { fetch('/api/x').then(r => r.json()).then(setData) }, [])
  console.log(items)
  const Row = () => <div/>
  return <ul>{items.map((it, i) => <li key={i}>{it}</li>)}{items.map(it => <Row />)}<img src="/a.png"/></ul>
}
"""
GOOD_PAGE = """import Image from 'next/image'
export default async function Page() {
  const items = await getItems()
  return <ul>{items.map((it) => <li key={it.id}>{it.name}</li>)}<Image src="/a.png" width={10} height={10} alt="" /></ul>
}
"""


def run_on(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, body in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(rel)) or d, exist_ok=True)
            with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write(body)
        return {f[1] for f in fe_check.run(d)}


if __name__ == "__main__":
    pkg = {"package.json": '{"dependencies": {"next": "x"}}'}
    got = run_on({**pkg, "app/page.tsx": BAD_PAGE})
    want = {"client-page", "ts-ignore", "any-type", "effect-sets-state", "fetch-in-effect", "console-log",
            "inner-component", "index-key", "missing-key", "raw-img"}
    assert want <= got, sorted(want - got)
    got = run_on({**pkg, "app/page.tsx": GOOD_PAGE})
    assert not got, sorted(got)
    print("selftest OK")
