#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'app'
cat > 'package.json' <<'J'
{ "name": "signup", "private": true, "dependencies": { "next": "16.0.0", "react": "19.2.0", "tailwindcss": "4.1.0" } }
J
cat > 'app/layout.tsx' <<'J'
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body>{children}</body></html>);
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
