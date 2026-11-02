import { requireUser } from '@/lib/auth';
import { handleError, HttpError } from '@/lib/http';
import { MAX_UPLOAD_BYTES, saveUpload } from '@/lib/upload';

const MULTIPART_OVERHEAD = 16 * 1024;

// POST multipart/form-data with one `file` field → 201 { key, mime, size }.
export async function POST(req: Request) {
  const requestId = crypto.randomUUID();
  try {
    await requireUser(); // ADAPT: keep the returned user to record the owner (below)

    // Reject oversized bodies before reading them into memory.
    const length = Number(req.headers.get('content-length'));
    if (!length) throw new HttpError(411, 'Content-Length required');
    if (length > MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD) throw new HttpError(413, 'File too large');

    const form = await req.formData().catch(() => {
      throw new HttpError(400, 'Expected multipart/form-data');
    });
    const file = form.get('file');
    if (!(file instanceof File)) throw new HttpError(400, 'Missing file field');

    const saved = await saveUpload(new Uint8Array(await file.arrayBuffer()));
    // ADAPT: record { key: saved.key, ownerId: user.id } in your DB; downloads must check that owner.
    return Response.json(saved, { status: 201 });
  } catch (e) {
    return handleError(e, requestId);
  }
}
