import { mkdtempSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { signIn } from '@/test/fake-auth';
import { POST } from '@/app/api/uploads/route';
import { MAX_UPLOAD_BYTES, sniff } from '@/lib/upload';

vi.mock('@/lib/auth', async () => (await import('@/test/fake-auth')).fakeAuth);

const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 13]);
let dir: string;

async function upload(parts: { bytes?: Uint8Array<ArrayBuffer>; name?: string; type?: string } | null, headers: Record<string, string> = {}) {
  const form = new FormData();
  if (parts) form.set('file', new File([parts.bytes ?? PNG], parts.name ?? 'a.png', { type: parts.type ?? 'image/png' }));
  const encoded = new Response(form);
  const body = new Uint8Array(await encoded.arrayBuffer());
  return POST(new Request('http://test/api/uploads', {
    method: 'POST',
    body,
    headers: { 'content-type': encoded.headers.get('content-type')!, 'content-length': String(body.byteLength), ...headers },
  }));
}

beforeEach(() => {
  dir = mkdtempSync(path.join(tmpdir(), 'uploads-'));
  vi.stubEnv('UPLOAD_DIR', dir);
  signIn('user_a');
});
afterEach(() => {
  rmSync(dir, { recursive: true, force: true });
  vi.unstubAllEnvs();
});

describe('POST /api/uploads', () => {
  it('requires a session', async () => {
    signIn(null);
    expect((await upload({})).status).toBe(401);
  });

  it('stores a real PNG under a random server-side name, ignoring the client name', async () => {
    const res = await upload({ name: '../../../etc/evil.png' });
    expect(res.status).toBe(201);
    const body = await res.json();
    expect(body).toMatchObject({ mime: 'image/png', size: PNG.byteLength });
    expect(body.key).toMatch(/^[0-9a-f-]{36}\.png$/);
    expect(readdirSync(dir)).toEqual([body.key]);
  });

  it('rejects content that is not in the allowlist even with an image name and MIME type', async () => {
    const html = new TextEncoder().encode('<html><script>alert(1)</script></html>');
    const res = await upload({ bytes: html, name: 'cat.png', type: 'image/png' });
    expect(res.status).toBe(415);
    expect(readdirSync(dir)).toEqual([]);
  });

  it('rejects an oversized body from its Content-Length before reading it', async () => {
    expect((await upload({}, { 'content-length': String(MAX_UPLOAD_BYTES * 2) })).status).toBe(413);
  });

  it('rejects an oversized file', async () => {
    const big = new Uint8Array(MAX_UPLOAD_BYTES + 1);
    big.set(PNG);
    expect((await upload({ bytes: big })).status).toBe(413);
  });

  it('rejects a request without the file field', async () => {
    expect((await upload(null)).status).toBe(400);
  });
});

describe('sniff', () => {
  it('detects types by magic bytes only', () => {
    expect(sniff(new Uint8Array([0xff, 0xd8, 0xff, 0xe0]))?.mime).toBe('image/jpeg');
    expect(sniff(new TextEncoder().encode('RIFF\0\0\0\0WEBPVP8 '))?.mime).toBe('image/webp');
    expect(sniff(new TextEncoder().encode('RIFF\0\0\0\0WAVEfmt '))).toBeNull();
    expect(sniff(new TextEncoder().encode('%PDF-1.7'))?.mime).toBe('application/pdf');
    expect(sniff(new TextEncoder().encode('<svg xmlns="http://www.w3.org/2000/svg"/>'))).toBeNull();
  });
});
