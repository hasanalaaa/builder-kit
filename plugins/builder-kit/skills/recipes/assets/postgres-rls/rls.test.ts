import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fakeDb, freshDb } from '@/test/fake-db';
import { withUser } from '@/lib/rls';

vi.mock('@/lib/db', async () => (await import('@/test/fake-db')).fakeDb);

type Doc = { id: string; owner_id: string; title: string };
let docId: string;

beforeEach(async () => {
  const pg = await freshDb('db/migrations/documents_rls.sql');
  await pg.exec('set role app_user'); // from here on, act like the app's connection, not the superuser
  docId = await withUser('user_a', async (db) =>
    (await db.query<Doc>("insert into documents (title) values ('a private doc') returning id")).rows[0].id);
});

describe('documents RLS', () => {
  it('lets the owner read their row and stamps owner_id from the session', async () => {
    const rows = await withUser('user_a', async (db) => (await db.query<Doc>('select * from documents')).rows);
    expect(rows).toEqual([expect.objectContaining({ id: docId, owner_id: 'user_a' })]);
  });

  it("hides user A's rows from user B, even by id", async () => {
    const rows = await withUser('user_b', async (db) =>
      (await db.query('select * from documents where id = $1', [docId])).rows);
    expect(rows).toEqual([]);
  });

  it("does not let user B update or delete user A's rows", async () => {
    await withUser('user_b', async (db) => {
      expect((await db.query("update documents set title = 'pwned' where id = $1 returning id", [docId])).rows).toEqual([]);
      expect((await db.query('delete from documents where id = $1 returning id', [docId])).rows).toEqual([]);
    });
    const still = await withUser('user_a', async (db) => (await db.query<Doc>('select title from documents')).rows);
    expect(still).toEqual([{ title: 'a private doc' }]);
  });

  it('does not let user B write rows owned by someone else', async () => {
    await expect(withUser('user_b', (db) =>
      db.query("insert into documents (owner_id, title) values ('user_a', 'planted')"))).rejects.toThrow(/row-level security/);
    await expect(withUser('user_b', async (db) => {
      const mine = (await db.query<Doc>("insert into documents (title) values ('mine') returning id")).rows[0];
      await db.query("update documents set owner_id = 'user_a' where id = $1", [mine.id]);
    })).rejects.toThrow(/row-level security/);
  });

  it('sees nothing and writes nothing without a user (fail closed)', async () => {
    expect((await fakeDb.db.query('select * from documents')).rows).toEqual([]);
    await expect(fakeDb.db.query("insert into documents (title) values ('x')")).rejects.toThrow();
    expect(() => withUser('', async () => null)).toThrow();
  });
});
