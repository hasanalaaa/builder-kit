import { z } from 'zod';
import { requireUser } from '@/lib/auth';
import { handleError, HttpError, readJson } from '@/lib/http';
import { deleteNote, getNote, NotePatch, updateNote } from '@/features/notes/notes';

type Ctx = { params: Promise<{ id: string }> };

// Another user's id and a malformed id both answer 404: never confirm that an id exists.
async function noteId(ctx: Ctx) {
  const id = z.uuid().safeParse((await ctx.params).id);
  if (!id.success) throw new HttpError(404, 'Not found');
  return id.data;
}

export async function GET(_req: Request, ctx: Ctx) {
  const requestId = crypto.randomUUID();
  try {
    const user = await requireUser();
    const note = await getNote(user.id, await noteId(ctx));
    if (!note) throw new HttpError(404, 'Not found');
    return Response.json(note);
  } catch (e) {
    return handleError(e, requestId);
  }
}

export async function PATCH(req: Request, ctx: Ctx) {
  const requestId = crypto.randomUUID();
  try {
    const user = await requireUser();
    const id = await noteId(ctx);
    const patch = await readJson(req, NotePatch);
    const note = await updateNote(user.id, id, patch);
    if (!note) throw new HttpError(404, 'Not found');
    return Response.json(note);
  } catch (e) {
    return handleError(e, requestId);
  }
}

export async function DELETE(_req: Request, ctx: Ctx) {
  const requestId = crypto.randomUUID();
  try {
    const user = await requireUser();
    if (!(await deleteNote(user.id, await noteId(ctx)))) throw new HttpError(404, 'Not found');
    return new Response(null, { status: 204 });
  } catch (e) {
    return handleError(e, requestId);
  }
}
