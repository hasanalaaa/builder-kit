import { z } from 'zod';
import { db } from '@/lib/db';

// ADAPT: fields of your resource. strict(): unknown keys (user_id, id, role…) are rejected, not ignored.
export const NoteCreate = z.object({
  title: z.string().trim().min(1).max(200),
  body: z.string().max(10_000).default(''),
}).strict();

export const NotePatch = z.object({
  title: z.string().trim().min(1).max(200),
  body: z.string().max(10_000),
}).partial().strict().refine((p) => Object.keys(p).length > 0, 'Nothing to update');

export const ListQuery = z.object({
  limit: z.coerce.number().int().min(1).max(100).default(20), // hard cap on page size
  cursor: z.uuid().optional(),
});

export type Note = { id: string; title: string; body: string; created_at: Date; updated_at: Date };

// Every query takes the owner id from the session and filters on it. Selected columns never include user_id.
export async function listNotes(userId: string, { limit, cursor }: z.infer<typeof ListQuery>) {
  const { rows } = await db.query<Note>(
    `select id, title, body, created_at, updated_at from notes
     where user_id = $1
       and ($2::uuid is null or (created_at, id) < (select created_at, id from notes where id = $2 and user_id = $1))
     order by created_at desc, id desc
     limit $3`,
    [userId, cursor ?? null, limit + 1],
  );
  return { items: rows.slice(0, limit), nextCursor: rows.length > limit ? rows[limit - 1].id : null };
}

export async function getNote(userId: string, id: string) {
  const { rows } = await db.query<Note>(
    'select id, title, body, created_at, updated_at from notes where id = $1 and user_id = $2',
    [id, userId],
  );
  return rows[0] ?? null;
}

export async function createNote(userId: string, input: z.infer<typeof NoteCreate>) {
  const { rows } = await db.query<Note>(
    'insert into notes (user_id, title, body) values ($1, $2, $3) returning id, title, body, created_at, updated_at',
    [userId, input.title, input.body],
  );
  return rows[0];
}

export async function updateNote(userId: string, id: string, patch: z.infer<typeof NotePatch>) {
  const { rows } = await db.query<Note>(
    `update notes set title = coalesce($3, title), body = coalesce($4, body), updated_at = now()
     where id = $1 and user_id = $2
     returning id, title, body, created_at, updated_at`,
    [id, userId, patch.title ?? null, patch.body ?? null],
  );
  return rows[0] ?? null;
}

export async function deleteNote(userId: string, id: string) {
  const { rows } = await db.query('delete from notes where id = $1 and user_id = $2 returning id', [id, userId]);
  return rows.length > 0;
}
