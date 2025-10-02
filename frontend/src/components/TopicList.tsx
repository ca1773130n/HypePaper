import React from 'react'

interface Topic {
  id: string
  name: string
  description?: string
  paper_count: number
  created_at: string
}

interface TopicListProps {
  topics: Topic[]
  watchedTopics: string[]
  onAddTopic: (topicId: string) => void
}

const TopicList: React.FC<TopicListProps> = ({ topics, watchedTopics, onAddTopic }) => {
  return (
    <div className="space-y-2">
      {topics.map((topic) => {
        const isWatched = watchedTopics.includes(topic.id)

        return (
          <div
            key={topic.id}
            className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors bg-white"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 capitalize">
                  {topic.name}
                </h3>
                {topic.description && (
                  <p className="text-sm text-gray-600 mt-1">{topic.description}</p>
                )}
                <p className="text-sm text-gray-500 mt-2">
                  {topic.paper_count} {topic.paper_count === 1 ? 'paper' : 'papers'}
                </p>
              </div>

              <button
                onClick={() => onAddTopic(topic.id)}
                disabled={isWatched}
                className={`ml-4 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isWatched
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
                aria-label={isWatched ? 'Already watching' : 'Add topic'}
              >
                {isWatched ? 'Watching' : 'Add'}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default TopicList
