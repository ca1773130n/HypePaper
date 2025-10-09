'use client';

import { SessionProvider } from 'next-auth/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { trpc } from '../lib/trpc';
import { useState } from 'react';
import { HeroUIProvider } from "@heroui/react";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        // You can add any links here if not already configured in lib/trpc.ts
        // For now, assuming links are configured in lib/trpc.ts
        // If not, you might need httpBatchLink here:
        // httpBatchLink({ url: 'http://localhost:10003/api/trpc' }),
      ],
    }),
  );

  return (
    <HeroUIProvider>
      <SessionProvider>
        <trpc.Provider client={trpcClient} queryClient={queryClient}>
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        </trpc.Provider>
      </SessionProvider>
    </HeroUIProvider>
  );
}
