'use client';

import { useSession, signIn, signOut } from 'next-auth/react';
import Link from 'next/link';
import { Button, Navbar, NavbarBrand, NavbarContent, NavbarItem } from "@heroui/react";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();

  return (
    <div className="flex flex-col min-h-screen w-full">
      <Navbar className="bg-gray-800 text-white shadow-lg">
        <NavbarBrand>
          <p className="font-bold text-inherit text-xl">Paper Explorer</p>
        </NavbarBrand>
        <NavbarContent justify="end">
          {session ? (
            <NavbarItem>
              <Button onClick={() => signOut({ callbackUrl: '/' })} color="default" variant="flat">
                Sign Out
              </Button>
            </NavbarItem>
          ) : (
            <NavbarItem>
              <Button onClick={() => signIn('google')} color="primary" variant="flat">
                Sign In
              </Button>
            </NavbarItem>
          )}
        </NavbarContent>
      </Navbar>

      <div className="flex flex-1">
        <aside className="w-64 bg-gray-800 text-white flex-shrink-0 p-4 border-r border-gray-700">
          <nav className="mt-4 space-y-2">
            <ul>
              <li><Link href="/" className="block p-2 text-gray-300 hover:bg-gray-700 rounded-md transition-colors duration-200">Top Papers</Link></li>
              <li><Link href="/subgraph" className="block p-2 text-gray-300 hover:bg-gray-700 rounded-md transition-colors duration-200">Topic Subgraphs</Link></li>
              <li><Link href="/crawler" className="block p-2 text-gray-300 hover:bg-gray-700 rounded-md transition-colors duration-200">Crawler Tasks</Link></li>
              {session && (
                <li><Link href="/profile" className="block p-2 text-gray-300 hover:bg-gray-700 rounded-md transition-colors duration-200">Profile</Link></li>
              )}
            </ul>
          </nav>
        </aside>
        <main className="flex-1 p-8 bg-gray-50 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

