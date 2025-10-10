import { initTRPC } from '@trpc/server';
import { z } from 'zod';

const t = initTRPC.create();

export const router = t.router;
export const publicProcedure = t.procedure;

export const appRouter = router({
  users: router({
    createUser: publicProcedure
      .input(z.object({ google_id: z.string(), username: z.string(), settings: z.record(z.string(), z.any()).optional() }))
      .mutation(async ({ input }) => {
        const response = await fetch('http://localhost:10003/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(input),
        });
        const data = await response.json();
        return data;
      }),
    getUser: publicProcedure
      .input(z.string())
      .query(async ({ input: google_id }) => {
        const response = await fetch(`http://localhost:10003/users/${google_id}`);
        const data = await response.json();
        return data;
      }),
    updateSettings: publicProcedure
      .input(z.object({ google_id: z.string(), settings: z.record(z.string(), z.any()) }))
      .mutation(async ({ input }) => {
        const response = await fetch(`http://localhost:10003/users/${input.google_id}/settings`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(input.settings),
        });
        const data = await response.json();
        return data;
      }),
  }),
  papers: router({
    top: publicProcedure
      .input(z.object({ limit: z.number().optional() }))
      .query(async ({ input }) => {
        const limit = input.limit !== undefined ? input.limit : 10;
        const response = await fetch(`http://localhost:10003/papers/top?limit=${limit}`);
        const data = await response.json();
        return data;
      }),
  }),
  getCrawlerTasks: publicProcedure
    .input(z.object({ google_id: z.string() }))
    .query(async ({ input }) => {
      // Proxy to FastAPI backend
      const response = await fetch('http://localhost:10003/trpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method: 'getCrawlerTasks', params: input }),
      });
      const data = await response.json();
      return data.result;
    }),
  createCrawlerTask: publicProcedure
    .input(
      z.object({
        google_id: z.string(),
        task: z.object({
          id: z.number(),
          user_id: z.string(),
          config: z.object({
            url: z.string(),
            depth: z.number(),
            max_papers: z.number(),
          }),
          status: z.string(),
          created_at: z.string(),
        }),
      }),
    )
    .mutation(async ({ input }) => {
      // Proxy to FastAPI backend
      const response = await fetch('http://localhost:10003/trpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method: 'createCrawlerTask', params: input }),
      });
      const data = await response.json();
      return data.result;
    }),
});

export type AppRouter = typeof appRouter;