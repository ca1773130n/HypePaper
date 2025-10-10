'use client';

import { SessionProvider } from 'next-auth/react';
import { trpc } from '../lib/trpc';

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider
      session={{
        strategy: 'jwt',
        jwtFromRequest: (req) => req.headers.authorization?.replace('Bearer ', ''),
      }}
      authentication={{
        jwt: {
          secret: 'your-secret-key',
          signingKey: 'ES256',
        },
      }}
    >
      {children}
    </SessionProvider>
  );
}
