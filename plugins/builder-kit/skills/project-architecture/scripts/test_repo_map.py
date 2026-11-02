#!/usr/bin/env python3
"""Self-test for repo_map.py: symbols per stack, ignores, budget truncation, cache hit/invalidate, no-git. Run: python3 test_repo_map.py"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repo_map  # noqa: E402

FIXTURE = {
    "package.json": '{"dependencies": {"next": "15.0.0", "react": "19.0.0"}}',
    "package-lock.json": "{}",
    ".gitignore": "ignored/\n",
    "ignored/hidden.ts": "export const secretThing = 1;\n",
    "node_modules/x/index.js": "exports.vendored = 1;\n",
    "public/logo.png": "png",
    "app/api/users/[id]/route.ts": "export async function GET() {}\nexport const POST = async () => {};\n",
    "app/(marketing)/about/page.tsx": "export default function About() { return null }\n",
    "src/lib/math.ts": "export function add(a, b) { return a + b }\nconst sub = 1;\nexport { sub as minus };\n",
    "src/lib/math.test.ts": "test('x', () => {})\n",
    "src/types.d.ts": "export interface Generated {}\n",
    "supabase/migrations/001_init.sql": "create table if not exists public.profiles (id uuid);\nCREATE TABLE orders (id int);\n",
    "billing/service.py": "def charge(x):\n    def inner():\n        pass\nclass Invoice:\n    def total(self):\n        pass\ndef _private():\n    pass\n",
    "billing/test_service.py": "def test_charge():\n    pass\n",
    "server/main.go": "package main\nfunc Serve() {}\nfunc helper() {}\ntype Store struct{}\nfunc (s *Store) Get() {}\n",
    "ios/ContentView.swift": "import SwiftUI\nstruct ContentView: View {}\n",
    "android/Main.kt": "data class User(val id: Int)\nobject Api\n",
    "lib/main.dart": "class HomePage extends StatelessWidget {}\n",
}


def write(root, files):
    for rel, body in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)


def git_init(root):
    subprocess.run(["git", "-C", root, "init", "-q"], check=True, capture_output=True)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        git_init(d)
        write(d, FIXTURE)
        text = repo_map.repo_map(d, refresh=True)
        for want in ("stack: Node, Next.js, React", "route.ts: GET,POST /api/users/[id]", "page.tsx: page /about",
                     "001_init.sql: public.profiles orders", "service.py: charge Invoice", "math.ts: add minus",
                     "main.go: Serve Store Get", "ContentView.swift: ContentView", "Main.kt: User Api", "main.dart: HomePage",
                     "tests: math.test.ts", "tests: test_service.py", "entry: android/Main.kt, lib/main.dart, server/main.go"):
            assert want in text, (want, text)
        for unwanted in ("hidden.ts", "secretThing", "node_modules", "vendored", "package-lock", "logo.png", "_private", "helper",
                         "inner", "test_charge", "types.d.ts"):
            assert unwanted not in text, (unwanted, text)
        assert repo_map.build(d, repo_map.bk.walk(d, ignore=repo_map.SKIP_DIRS), 2500) == text, "output must be stable"

        cache = os.path.join(d, ".git", "builder-kit", "map.txt")
        assert os.path.exists(cache)
        with open(cache, encoding="utf-8") as f:
            cached = f.read()
        with open(cache, "w", encoding="utf-8") as f:
            f.write(cached + "\nCACHED")
        assert repo_map.repo_map(d).endswith("CACHED"), "unchanged tree must hit the cache"
        assert not repo_map.repo_map(d, refresh=True).endswith("CACHED"), "--refresh must rebuild"
        with open(cache, "w", encoding="utf-8") as f:
            f.write(cached + "\nCACHED")
        os.utime(os.path.join(d, "billing", "service.py"), (1, 1))
        assert not repo_map.repo_map(d).endswith("CACHED"), "a changed mtime must invalidate the cache"

        write(d, {f"big/mod{i:03}.ts": f"export function handler{i}() {{}}\n" for i in range(400)})
        small = repo_map.repo_map(d, max_tokens=300, refresh=True)
        assert len(small) <= 300 * 4 + 400 and "more files" in small and "big/" in small, (len(small), small)
        cli = subprocess.run([sys.executable, os.path.join(HERE, "repo_map.py"), d, "--max-tokens", "300"], capture_output=True, text=True)
        assert cli.returncode == 0 and cli.stdout.strip() == small, cli

    with tempfile.TemporaryDirectory() as d:
        write(d, {"main.py": "def run():\n    pass\n", ".hidden/x.py": "def nope():\n    pass\n", "dist/y.js": "exports.z = 1;\n"})
        text = repo_map.repo_map(d)
        assert "main.py: run" in text and "nope" not in text and "y.js" not in text, text
        assert repo_map.cache_path(d) is None and not os.path.exists(os.path.join(d, ".git"))
    print("selftest OK")
