import { randomUUID } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { env } from '@/lib/env';
import { HttpError } from '@/lib/http';

export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024; // ADAPT: size cap; also cap it at your proxy / bucket policy

// ADAPT: the allowlist. The type is decided by the file's first bytes, never by the client's MIME type or name.
// No HTML, SVG or JS: they run in the browser when served from your origin.
const TYPES = [
  { mime: 'image/png', ext: 'png', magic: [[0, [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]]] },
  { mime: 'image/jpeg', ext: 'jpg', magic: [[0, [0xff, 0xd8, 0xff]]] },
  { mime: 'image/webp', ext: 'webp', magic: [[0, [0x52, 0x49, 0x46, 0x46]], [8, [0x57, 0x45, 0x42, 0x50]]] }, // RIFF....WEBP
  { mime: 'application/pdf', ext: 'pdf', magic: [[0, [0x25, 0x50, 0x44, 0x46, 0x2d]]] }, // %PDF-
] as const;

export function sniff(bytes: Uint8Array) {
  return TYPES.find((t) => t.magic.every(([offset, sig]) => sig.every((b, i) => bytes[offset + i] === b))) ?? null;
}

export async function saveUpload(bytes: Uint8Array) {
  if (bytes.byteLength === 0) throw new HttpError(400, 'Empty file');
  if (bytes.byteLength > MAX_UPLOAD_BYTES) throw new HttpError(413, 'File too large');
  const type = sniff(bytes);
  if (!type) throw new HttpError(415, 'Unsupported file type');

  // The stored name is generated here; nothing from the client reaches the path, so no traversal is possible.
  const key = `${randomUUID()}.${type.ext}`;
  // ADAPT: swap for a private object-storage put (S3/R2/GCS) and serve via short-lived signed URLs.
  // turbopackIgnore: a runtime data folder, not source to bundle.
  const dir = path.resolve(/*turbopackIgnore: true*/ env('UPLOAD_DIR')); // a private folder, never under public/
  await mkdir(dir, { recursive: true });
  await writeFile(path.join(/*turbopackIgnore: true*/ dir, key), bytes, { flag: 'wx' }); // wx: never overwrite
  return { key, mime: type.mime, size: bytes.byteLength };
}
