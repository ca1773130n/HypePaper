import NextAuth, { DefaultSession, DefaultUser, User } from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import type { Account, Profile } from 'next-auth';
import type { JWT } from 'next-auth/jwt';
import { appRouter } from '../../../../server/trpc';

const createContext = async () => ({}); // You might need a more complex context depending on your tRPC setup

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }: { user: User, account: Account | null, profile?: Profile }) {
      if (account?.provider === 'google') {
        const caller = appRouter.createCaller(await createContext());
        await caller.users.createUser({
          google_id: account.providerAccountId,
          username: user.email || user.name || 'user_' + account.providerAccountId,
          settings: {},
        });
      }
      return true;
    },
    async jwt({ token, account, profile }: { token: JWT, account: Account | null, profile?: Profile }) {
      if (account) {
        token.google_id = account.providerAccountId;
      }
      return token;
    },
    async session({ session, token }: { session: any, token: JWT }) {
      session.user.google_id = token.google_id;
      const caller = appRouter.createCaller(await createContext());
      const user = await caller.users.getUser(token.google_id as string);
      session.user.id = user.id;
      session.user.username = user.username;
      session.user.settings = user.settings;
      return session;
    },
  },
});

export { handler as GET, handler as POST };
