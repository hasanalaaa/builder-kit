import { requireUser } from '@/lib/auth';
import { handleError, parse, readJson } from '@/lib/http';
import { createNote, listNotes, ListQuery, NoteCreate } from '@/features/notes/notes';

// GET /api/notes?limit=20&cursor=<id> → { items, nextCursor }
export async function GET(req: Request) {
  const requestId = crypto.randomUUID();
  try {
    const user = await requireUser();
    const query = parse(ListQuery, Object.fromEntries(new URL(req.url).searchParams));
    return Response.json(await listNotes(user.id, query));
  } catch (e) {
    return handleError(e, requestId);
  }
}

// POST /api/notes { title, body? } → 201 note
export async function POST(req: Request) {
  const requestId = crypto.randomUUID();
  try {
    const user = await requireUser();
    const input = await readJson(req, NoteCreate);
    return Response.json(await createNote(user.id, input), { status: 201 });
  } catch (e) {
    return handleError(e, requestId);
  }
}
