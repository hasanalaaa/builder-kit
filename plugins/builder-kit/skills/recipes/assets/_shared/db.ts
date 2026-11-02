import { Pool, type QueryResultRow } from 'pg';
import { env } from '@/lib/env';

export type Queryable = {
  query<R extends QueryResultRow = QueryResultRow>(text: string, params?: unknown[]): Promise<{ rows: R[] }>;
};

let pool: Pool | undefined;
const getPool = () => (pool ??= new Pool({ connectionString: env('DATABASE_URL'), max: 10 }));

// Parameterized queries only: values go in `params`, never into the SQL string.
export const db: Queryable = {
  query: (text, params) => getPool().query(text, params),
};

export async function tx<T>(fn: (client: Queryable) => Promise<T>): Promise<T> {
  const client = await getPool().connect();
  try {
    await client.query('begin');
    const result = await fn(client);
    await client.query('commit');
    return result;
  } catch (e) {
    try {
      await client.query('rollback');
    } catch (rollbackError) {
      console.error('rollback failed', rollbackError); // keep throwing the original error below
    }
    throw e;
  } finally {
    client.release();
  }
}
