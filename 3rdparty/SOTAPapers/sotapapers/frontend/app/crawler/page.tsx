'use client';

import { useSession } from 'next-auth/react';
import { trpc } from '@/lib/trpc';
import { useState } from 'react';

interface CrawlerTask {
  id: number;
  user_id: string; // Changed to string to match backend schema
  config: { [key: string]: any }; // Adjust with a more specific type if known
  status: string;
  created_at: string;
}

export default function CrawlerTasks() {
  const { data: session, status } = useSession();

  // Safely get google_id and user.id
  const googleId = session?.user?.google_id;
  const userId = session?.user?.id;

  const [taskConfig, setTaskConfig] = useState({ url: 'arxiv.org', depth: 2, max_papers: 100 });

  const { data: tasks, isLoading } = trpc.getCrawlerTasks.useQuery(
    { google_id: googleId || '' },
    { enabled: status === 'authenticated' && !!googleId }
  );

  const createTask = trpc.createCrawlerTask.useMutation();

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (googleId && userId) {
      await createTask.mutate({
        google_id: googleId,
        task: { id: Date.now(), user_id: String(userId), config: taskConfig, status: 'pending', created_at: new Date().toISOString() },
      });
    }
  };

  if (status === 'loading') {
    return <p className="container mx-auto p-4">Loading session...</p>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Crawler Tasks</h1>
      {status === 'authenticated' && session?.user ? (
        <>
          <form onSubmit={handleCreateTask} className="mb-4 space-y-4">
            <input
              type="text"
              placeholder="Crawler URL"
              value={taskConfig.url}
              onChange={(e) => setTaskConfig({ ...taskConfig, url: e.target.value })}
              className="border p-2 w-full"
            />
            <input
              type="number"
              placeholder="Depth"
              value={taskConfig.depth}
              onChange={(e) => setTaskConfig({ ...taskConfig, depth: parseInt(e.target.value) })}
              className="border p-2 w-full"
            />
            <input
              type="number"
              placeholder="Max Papers"
              value={taskConfig.max_papers}
              onChange={(e) => setTaskConfig({ ...taskConfig, max_papers: parseInt(e.target.value) })}
              className="border p-2 w-full"
            />
            <button type="submit" className="bg-blue-500 text-white p-2 rounded">Create Task</button>
          </form>
          {isLoading ? (
            <p>Loading...</p>
          ) : (
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="border p-2">ID</th>
                  <th className="border p-2">Config</th>
                  <th className="border p-2">Status</th>
                  <th className="border p-2">Created At</th>
                </tr>
              </thead>
              <tbody>
                {tasks?.map((task: CrawlerTask) => (
                  <tr key={task.id}>
                    <td className="border p-2">{task.id}</td>
                    <td className="border p-2">{JSON.stringify(task.config)}</td>
                    <td className="border p-2">{task.status}</td>
                    <td className="border p-2">{task.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      ) : (
        <p>Please sign in with Google to view crawler tasks.</p>
      )}
    </div>
  );
}