import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TrendChart from '../../src/components/TrendChart'

describe('TrendChart', () => {
  const mockMetrics = [
    { snapshot_date: '2025-01-01', github_stars: 100, citation_count: 10 },
    { snapshot_date: '2025-01-08', github_stars: 150, citation_count: 12 },
    { snapshot_date: '2025-01-15', github_stars: 200, citation_count: 15 },
    { snapshot_date: '2025-01-22', github_stars: 300, citation_count: 18 },
  ]

  it('renders chart container', () => {
    render(<TrendChart metrics={mockMetrics} />)
    // Recharts renders SVG elements
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('displays chart with metrics data', () => {
    const { container } = render(<TrendChart metrics={mockMetrics} />)
    // Recharts should render the data
    expect(container.querySelector('.recharts-wrapper')).toBeInTheDocument()
  })

  it('shows empty state when no metrics provided', () => {
    render(<TrendChart metrics={[]} />)
    expect(screen.getByText(/no data|no metrics/i)).toBeInTheDocument()
  })

  it('renders both stars and citations lines', () => {
    const { container } = render(<TrendChart metrics={mockMetrics} />)
    // Should have two lines (stars and citations)
    const lines = container.querySelectorAll('.recharts-line')
    expect(lines.length).toBe(2)
  })
})
