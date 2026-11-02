import { tx, type Queryable } from '@/lib/db';

// Run queries as `userId` under RLS. set_config(..., true) is transaction-local, so the id can never leak to
// the next request that reuses this pooled connection.
export function withUser<T>(userId: string, fn: (db: Queryable) => Promise<T>): Promise<T> {
  if (!userId) throw new Error('withUser needs the verified session user id');
  return tx(async (db) => {
    await db.query("select set_config('app.user_id', $1, true)", [userId]);
    return fn(db);
  });
}
