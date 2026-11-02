import { HttpError } from '@/lib/http';

export type User = { id: string };

// ADAPT: back this with your auth provider's server-side check and return the verified user id, e.g.
//   Auth.js:  const s = await auth(); if (!s?.user?.id) throw new HttpError(401, 'Unauthorized'); return { id: s.user.id };
//   Clerk:    const { userId } = await auth(); if (!userId) throw ...; return { id: userId };
//   Supabase: const { data: { user } } = await supabase.auth.getUser(); if (!user) throw ...; return { id: user.id };
// The id must come from the verified session, never from the body, query string or a client-set header.
export async function requireUser(): Promise<User> {
  throw new HttpError(401, 'Unauthorized'); // fails closed until wired to a real session
}
