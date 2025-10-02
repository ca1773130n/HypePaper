import React, { useEffect, useState } from 'react'

const TopicManager: React.FC = () => {
  const [watchedTopics, setWatchedTopics] = useState<string[]>([])

  useEffect(() => {
    // Load watched topics from localStorage
    const stored = localStorage.getItem('watchedTopics')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setWatchedTopics(parsed)
      } catch (e) {
        console.error('Failed to parse watched topics:', e)
      }
    }
  }, [])

  const removeTopic = (topicId: string) => {
    const updated = watchedTopics.filter((id) => id !== topicId)
    setWatchedTopics(updated)
    localStorage.setItem('watchedTopics', JSON.stringify(updated))
  }

  if (watchedTopics.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-600">
          No topics watched yet. Add topics from the list below to start tracking trending papers.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Watched Topics</h2>
      <div className="flex flex-wrap gap-2">
        {watchedTopics.map((topicId) => (
          <div
            key={topicId}
            className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm"
          >
            <span className="capitalize">{topicId.replace(/-/g, ' ')}</span>
            <button
              onClick={() => removeTopic(topicId)}
              className="text-blue-600 hover:text-blue-800 font-bold"
              aria-label={`Remove ${topicId}`}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TopicManager
