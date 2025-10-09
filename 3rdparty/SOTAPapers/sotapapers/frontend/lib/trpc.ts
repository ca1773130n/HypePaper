import { createTRPCReact } from '@trpc/react-query';
import { httpBatchLink } from '@trpc/client';
import type { AppRouter } from '@/server/trpc';

export const trpc = createTRPCReact<AppRouter>({
  overrides: {
    links: [
      httpBatchLink({
        url: 'http://localhost:10003/api/trpc', // Points to Next.js API route
      }),
    ],
  },
});