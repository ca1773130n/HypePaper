import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import TrendChart from '../components/TrendChart'
import { papersService, PaperDetail, MetricSnapshot } from '../services/papersService'

const PaperDetailPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>()
  const navigate = useNavigate()
  const [paper, setPaper] = useState<PaperDetail | null>(null)
  const [metrics, setMetrics] = useState<MetricSnapshot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadPaperData = async () => {
      if (!paperId) {
        setError('Paper ID not provided')
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const [paperData, metricsData] = await Promise.all([
          papersService.getPaperById(paperId),
          papersService.getPaperMetrics(paperId, 30),
        ])

        setPaper(paperData)
        setMetrics(metricsData.metrics)
      } catch (err) {
        console.error('Failed to load paper data:', err)
        setError('Failed to load paper details. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    loadPaperData()
  }, [paperId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading paper details...</p>
      </div>
    )
  }

  if (error || !paper) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Paper not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:underline"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:underline mb-4 inline-block"
          >
            ← Back to Home
          </button>
          <h1 className="text-3xl font-bold text-gray-900">{paper.title}</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Authors and metadata */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <p className="text-gray-700 mb-4">{paper.authors.join(', ')}</p>

          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <span>Published: {new Date(paper.published_date).toLocaleDateString()}</span>
            {paper.venue && <span>• {paper.venue}</span>}
            {paper.arxiv_id && <span>• arXiv: {paper.arxiv_id}</span>}
            {paper.doi && <span>• DOI: {paper.doi}</span>}
          </div>

          <div className="mt-4 flex gap-4">
            {paper.github_url && (
              <a
                href={paper.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                GitHub →
              </a>
            )}
            {paper.arxiv_url && (
              <a
                href={paper.arxiv_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                arXiv →
              </a>
            )}
            {paper.pdf_url && (
              <a
                href={paper.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                PDF →
              </a>
            )}
          </div>
        </div>

        {/* Abstract */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Abstract</h2>
          <p className="text-gray-700 leading-relaxed">{paper.abstract}</p>
        </div>

        {/* Hype Score Breakdown */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Hype Score Breakdown</h2>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Overall Hype Score</span>
                <span className="text-2xl font-bold text-blue-600">{paper.hype_score.toFixed(1)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full"
                  style={{ width: `${paper.hype_score}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-600">7-Day Star Growth</p>
                <p className="text-lg font-semibold text-gray-900">
                  {(paper.star_growth_7d * 100).toFixed(1)}%
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-600">30-Day Citation Growth</p>
                <p className="text-lg font-semibold text-gray-900">
                  {(paper.citation_growth_30d * 100).toFixed(1)}%
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-600">Current Stars</p>
                <p className="text-lg font-semibold text-gray-900">{paper.current_stars}</p>
              </div>

              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-600">Trend</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">{paper.trend_label}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Trend Chart */}
        <TrendChart metrics={metrics} />
      </main>
    </div>
  )
}

export default PaperDetailPage
