import NextAuth, { DefaultSession, DefaultUser } from "next-auth";
import { JWT } from "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    user: {
      id: number | string;
      google_id: string;
      username: string;
      settings: Record<string, any>;
    } & DefaultSession["user"];
  }

  interface User extends DefaultUser {
    id: number | string;
    google_id: string;
    username: string;
    settings: Record<string, any>;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: number | string;
    google_id: string;
    username: string;
    settings: Record<string, any>;
  }
} 