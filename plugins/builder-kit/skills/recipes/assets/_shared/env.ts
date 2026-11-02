// Read a required server-side env var. Read lazily (inside handlers) so `next build` works without secrets.
// No fallbacks: a missing secret is a loud error, never a default value.
export function env(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env var ${name}`);
  return value;
}
