#!/usr/bin/env bash
set -euo pipefail
mkdir -p lib/supabase app/api/profile
cat > package.json <<'J'
{ "name": "profiles", "private": true, "dependencies": { "next": "16.0.0", "@supabase/supabase-js": "2.75.0", "@supabase/ssr": "0.7.0" } }
J
cat > lib/supabase/server.ts <<'J'
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
export async function supabaseServer() {
  const store = await cookies();
  return createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!, {
    cookies: { getAll: () => store.getAll(), setAll: (all) => all.forEach((c) => store.set(c.name, c.value, c.options)) },
  });
}
J
cat > app/api/profile/route.ts <<'J'
import { supabaseServer } from "@/lib/supabase/server";
export async function GET() {
  const supabase = await supabaseServer();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return new Response("Unauthorized", { status: 401 });
  const { data } = await supabase.from("profiles").select("*").eq("id", user.id).single();
  return Response.json(data);
}
J
git init -q && git add -A && git -c user.email=e@x -c user.name=e commit -qm init
