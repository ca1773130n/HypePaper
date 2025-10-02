import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface MetricData {
  snapshot_date: string
  github_stars: number | null
  citation_count: number | null
}

interface TrendChartProps {
  metrics: MetricData[]
}

const TrendChart: React.FC<TrendChartProps> = ({ metrics }) => {
  if (metrics.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-600">No metrics data available yet</p>
      </div>
    )
  }

  // Format data for Recharts
  const chartData = metrics.map((m) => ({
    date: new Date(m.snapshot_date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    stars: m.github_stars ?? 0,
    citations: m.citation_count ?? 0,
  }))

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Trend History</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="stars"
            stroke="#3b82f6"
            name="GitHub Stars"
            strokeWidth={2}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="citations"
            stroke="#10b981"
            name="Citations"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default TrendChart
