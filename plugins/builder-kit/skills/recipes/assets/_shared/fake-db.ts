// Test-only: real Postgres (PGlite, in-process WASM) behind the '@/lib/db' interface, so SQL, constraints,
// transactions and RLS run for real. In a test:
//   vi.mock('@/lib/db', async () => (await import('@/test/fake-db')).fakeDb);
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { PGlite } from '@electric-sql/pglite';
import type * as Db from '@/lib/db';

let pg: PGlite | undefined;
const current = () => {
  if (!pg) throw new Error('call freshDb() first');
  return pg;
};

// New empty database with the given migrations (paths relative to the project root) applied.
export async function freshDb(...migrations: string[]): Promise<PGlite> {
  pg = new PGlite();
  for (const file of migrations) await pg.exec(readFileSync(path.resolve(file), 'utf8'));
  return pg;
}

export const fakeDb: typeof Db = {
  db: { query: (text, params) => current().query(text, params) },
  tx: (fn) => current().transaction((t) => fn(t)),
};
