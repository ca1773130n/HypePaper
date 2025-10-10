'use client';

import { useSession } from 'next-auth/react';
import { trpc } from '../../lib/trpc';
import { useState } from 'react';

export default function Profile() {
  const { data: session } = useSession();
  const [settings, setSettings] = useState(session?.user.settings || {});
  const updateSettings = trpc.users.updateSettings.useMutation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (session?.user.google_id) {
      updateSettings.mutate({ google_id: session.user.google_id, settings });
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Profile</h1>
      {session ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p>Username: {session.user.username}</p>
          <textarea
            placeholder="User settings (JSON)"
            value={JSON.stringify(settings, null, 2)}
            onChange={(e) => setSettings(JSON.parse(e.target.value))}
            className="border p-2 w-full h-32"
          />
          <button type="submit" className="bg-blue-500 text-white p-2 rounded">
            Save Settings
          </button>
        </form>
      ) : (
        <p>Please sign in with Google to view your profile.</p>
      )}
    </div>
  );
}
