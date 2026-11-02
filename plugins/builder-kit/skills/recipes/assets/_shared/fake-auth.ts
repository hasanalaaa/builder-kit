// Test-only: a session you control. In a test:
//   vi.mock('@/lib/auth', async () => (await import('@/test/fake-auth')).fakeAuth);
//   signIn('user_a'); ...; signIn(null);
import type * as Auth from '@/lib/auth';
import { HttpError } from '@/lib/http';

let userId: string | null = null;
export const signIn = (id: string | null) => {
  userId = id;
};

export const fakeAuth: typeof Auth = {
  requireUser: async () => {
    if (!userId) throw new HttpError(401, 'Unauthorized');
    return { id: userId };
  },
};
