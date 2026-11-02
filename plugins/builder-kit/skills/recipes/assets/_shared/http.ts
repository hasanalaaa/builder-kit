import { z } from 'zod';

export class HttpError extends Error {
  constructor(
    public status: number,
    message: string,
    public extra: { fields?: unknown; retryAfterSec?: number } = {},
  ) {
    super(message);
  }
}

// One error shape for every route: { error, requestId, fields? }. Details of unexpected errors stay in server logs.
export function handleError(e: unknown, requestId: string): Response {
  if (e instanceof HttpError) {
    const headers: Record<string, string> = {};
    if (e.extra.retryAfterSec !== undefined) headers['Retry-After'] = String(e.extra.retryAfterSec);
    // bk-ignore: error-detail-leak (HttpError messages are written for the client; other errors take the generic branch)
    return Response.json({ error: e.message, requestId, fields: e.extra.fields }, { status: e.status, headers });
  }
  console.error(JSON.stringify({ requestId, error: String(e) }));
  return Response.json({ error: 'Something went wrong', requestId }, { status: 500 });
}

export function parse<T extends z.ZodType>(schema: T, data: unknown): z.infer<T> {
  const result = schema.safeParse(data);
  if (!result.success) throw new HttpError(400, 'Invalid input', { fields: z.flattenError(result.error).fieldErrors });
  return result.data;
}

const MAX_JSON_BYTES = 64 * 1024;

// JSON-only bodies: a cross-site <form> cannot send application/json without a CORS preflight (CSRF).
export async function readJson<T extends z.ZodType>(req: Request, schema: T): Promise<z.infer<T>> {
  if (!req.headers.get('content-type')?.startsWith('application/json')) throw new HttpError(415, 'Expected application/json');
  if (Number(req.headers.get('content-length') ?? 0) > MAX_JSON_BYTES) throw new HttpError(413, 'Body too large');
  const text = await req.text();
  if (text.length > MAX_JSON_BYTES) throw new HttpError(413, 'Body too large');
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new HttpError(400, 'Invalid JSON');
  }
  return parse(schema, data);
}
