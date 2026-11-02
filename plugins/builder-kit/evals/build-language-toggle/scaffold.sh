#!/usr/bin/env bash
set -euo pipefail
mkdir -p 'app' 'components'
cat > 'package.json' <<'J'
{ "name": "souq", "private": true, "dependencies": { "next": "16.0.0", "react": "19.2.0", "tailwindcss": "4.1.0" } }
J
cat > 'app/layout.tsx' <<'J'
import "./globals.css";
import Header from "@/components/Header";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-gray-900">
        <Header />
        {children}
      </body>
    </html>
  );
}
J
cat > 'app/globals.css' <<'J'
@import "tailwindcss";
J
cat > 'components/Header.tsx' <<'J'
export default function Header() {
  return (
    <header className="flex items-center border-b px-6 py-4">
      <a href="/" className="text-lg font-bold">Souq</a>
      <nav className="ml-auto flex gap-4 text-left">
        <a href="/products" className="pl-2">Products</a>
        <a href="/cart" className="mr-2">Cart</a>
      </nav>
    </header>
  );
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
