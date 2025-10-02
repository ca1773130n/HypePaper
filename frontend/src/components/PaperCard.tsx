import React from 'react'

interface PaperCardProps {
  paper: {
    id: string
    title: string
    authors: string[]
    published_date: string
    venue?: string
    github_url?: string
    hype_score: number
    trend_label: string
  }
}

const PaperCard: React.FC<PaperCardProps> = ({ paper }) => {
  const getTrendColor = (label: string) => {
    switch (label) {
      case 'rising':
        return 'text-green-600 bg-green-50'
      case 'declining':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getTrendIcon = (label: string) => {
    switch (label) {
      case 'rising':
        return '↗'
      case 'declining':
        return '↘'
      default:
        return '→'
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold text-gray-900 flex-1">
          <a href={`/papers/${paper.id}`} className="hover:text-blue-600">
            {paper.title}
          </a>
        </h3>
        <div className={`ml-4 px-2 py-1 rounded text-sm font-medium ${getTrendColor(paper.trend_label)}`}>
          {getTrendIcon(paper.trend_label)} {paper.trend_label}
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-2">
        {paper.authors.join(', ')}
      </p>

      <div className="flex items-center gap-4 text-sm text-gray-500">
        <span>{new Date(paper.published_date).toLocaleDateString()}</span>
        {paper.venue && <span>• {paper.venue}</span>}
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
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Hype Score</span>
          <div className="flex items-center gap-2">
            <div className="w-32 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${paper.hype_score}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-900">
              {paper.hype_score.toFixed(1)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PaperCard
