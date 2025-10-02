import React, { useEffect, useState } from 'react'
import PaperCard from '../components/PaperCard'
import TopicList from '../components/TopicList'
import TopicManager from '../components/TopicManager'
import { papersService, PaperListItem } from '../services/papersService'
import { topicsService, Topic } from '../services/topicsService'

const HomePage: React.FC = () => {
  const [papers, setPapers] = useState<PaperListItem[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [watchedTopics, setWatchedTopics] = useState<string[]>([])
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'hype_score' | 'recency' | 'stars'>('hype_score')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load watched topics from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('watchedTopics')
    if (stored) {
      try {
        setWatchedTopics(JSON.parse(stored))
      } catch (e) {
        console.error('Failed to parse watched topics:', e)
      }
    }
  }, [])

  // Load topics
  useEffect(() => {
    const loadTopics = async () => {
      try {
        const data = await topicsService.getTopics()
        setTopics(data.topics)
      } catch (err) {
        console.error('Failed to load topics:', err)
      }
    }

    loadTopics()
  }, [])

  // Load papers
  useEffect(() => {
    const loadPapers = async () => {
      setLoading(true)
      setError(null)

      try {
        const data = await papersService.getPapers({
          topic_id: selectedTopic ?? undefined,
          sort: sortBy,
          limit: 20,
        })
        setPapers(data.papers)
      } catch (err) {
        console.error('Failed to load papers:', err)
        setError('Failed to load papers. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    loadPapers()
  }, [selectedTopic, sortBy])

  const handleAddTopic = (topicId: string) => {
    const updated = [...watchedTopics, topicId]
    setWatchedTopics(updated)
    localStorage.setItem('watchedTopics', JSON.stringify(updated))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">HypePaper</h1>
          <p className="text-gray-600 mt-1">Track trending research papers</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column: Papers list */}
          <div className="lg:col-span-2">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-gray-900">
                {selectedTopic ? `Papers in ${selectedTopic}` : 'All Papers'}
              </h2>

              <div className="flex items-center gap-4">
                <label className="text-sm text-gray-600">Sort by:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                >
                  <option value="hype_score">Hype Score</option>
                  <option value="recency">Recent</option>
                  <option value="stars">GitHub Stars</option>
                </select>
              </div>
            </div>

            {loading && (
              <div className="text-center py-12">
                <p className="text-gray-600">Loading papers...</p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                {error}
              </div>
            )}

            {!loading && !error && papers.length === 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                <p className="text-gray-600">No papers found</p>
              </div>
            )}

            <div className="space-y-4">
              {papers.map((paper) => (
                <PaperCard key={paper.id} paper={paper} />
              ))}
            </div>
          </div>

          {/* Right column: Topics */}
          <div className="space-y-6">
            <TopicManager />

            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Topics</h2>
              <TopicList
                topics={topics}
                watchedTopics={watchedTopics}
                onAddTopic={handleAddTopic}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default HomePage
