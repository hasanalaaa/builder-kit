import { beforeEach, describe, expect, it, vi } from 'vitest';
import { freshDb } from '@/test/fake-db';
import { signIn } from '@/test/fake-auth';
import * as list from '@/app/api/notes/route';
import * as item from '@/app/api/notes/[id]/route';

vi.mock('@/lib/db', async () => (await import('@/test/fake-db')).fakeDb);
vi.mock('@/lib/auth', async () => (await import('@/test/fake-auth')).fakeAuth);

const URL_BASE = 'http://test/api/notes';
const json = (method: string, body: unknown) =>
  new Request(URL_BASE, { method, body: JSON.stringify(body), headers: { 'content-type': 'application/json' } });
const ctx = (id: string) => ({ params: Promise.resolve({ id }) });

async function create(title: string) {
  const res = await list.POST(json('POST', { title }));
  expect(res.status).toBe(201);
  return (await res.json()) as { id: string; title: string };
}

beforeEach(async () => {
  await freshDb('db/migrations/notes.sql');
  signIn('user_a');
});

describe('notes API', () => {
  it('requires a session on every method', async () => {
    signIn(null);
    expect((await list.GET(new Request(URL_BASE))).status).toBe(401);
    expect((await list.POST(json('POST', { title: 'x' }))).status).toBe(401);
    expect((await item.DELETE(new Request(URL_BASE), ctx(crypto.randomUUID()))).status).toBe(401);
  });

  it("never lets user B read, change or delete user A's note", async () => {
    const note = await create('a secret');
    signIn('user_b');
    expect((await item.GET(new Request(URL_BASE), ctx(note.id))).status).toBe(404);
    expect((await item.PATCH(json('PATCH', { title: 'pwned' }), ctx(note.id))).status).toBe(404);
    expect((await item.DELETE(new Request(URL_BASE), ctx(note.id))).status).toBe(404);
    expect((await (await list.GET(new Request(URL_BASE))).json()).items).toEqual([]);

    signIn('user_a');
    const mine = await (await item.GET(new Request(URL_BASE), ctx(note.id))).json();
    expect(mine.title).toBe('a secret');
    expect(mine).not.toHaveProperty('user_id');
  });

  it('rejects server-owned and unknown fields, and bad input, with field errors', async () => {
    const res = await list.POST(json('POST', { title: 'x', user_id: 'user_b' }));
    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ error: 'Invalid input' });
    expect((await list.POST(json('POST', { title: '' }))).status).toBe(400);
    expect((await list.POST(new Request(URL_BASE, { method: 'POST', body: '{"title":"x"}' }))).status).toBe(415);
    expect((await item.GET(new Request(URL_BASE), ctx('not-a-uuid'))).status).toBe(404);
  });

  it('updates only the given fields and deletes', async () => {
    const note = await create('old');
    const patched = await (await item.PATCH(json('PATCH', { body: 'new body' }), ctx(note.id))).json();
    expect(patched).toMatchObject({ title: 'old', body: 'new body' });
    expect((await item.PATCH(json('PATCH', {}), ctx(note.id))).status).toBe(400);
    expect((await item.DELETE(new Request(URL_BASE), ctx(note.id))).status).toBe(204);
    expect((await item.GET(new Request(URL_BASE), ctx(note.id))).status).toBe(404);
  });

  it('paginates with a capped page size', async () => {
    for (const t of ['1', '2', '3']) await create(t);
    const ids = (body: { items: { id: string }[] }) => body.items.map((n) => n.id);
    const all = ids(await (await list.GET(new Request(URL_BASE))).json());
    const page1 = await (await list.GET(new Request(`${URL_BASE}?limit=2`))).json();
    const page2 = await (await list.GET(new Request(`${URL_BASE}?limit=2&cursor=${page1.nextCursor}`))).json();
    // Same-timestamp rows are ordered by id, so compare pages with the full list, not with insertion order.
    expect([...ids(page1), ...ids(page2)]).toEqual(all);
    expect(all).toHaveLength(3);
    expect(page2.nextCursor).toBeNull();
    expect((await list.GET(new Request(`${URL_BASE}?limit=1000`))).status).toBe(400);
  });
});
