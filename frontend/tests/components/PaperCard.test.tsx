import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import PaperCard from '../../src/components/PaperCard'

describe('PaperCard', () => {
  const mockPaper = {
    id: '123',
    title: 'Neural Radiance Fields for View Synthesis',
    authors: ['Ben Mildenhall', 'Pratul P. Srinivasan', 'Matthew Tancik'],
    published_date: '2020-03-19',
    venue: 'ECCV 2020',
    github_url: 'https://github.com/bmild/nerf',
    arxiv_url: 'https://arxiv.org/abs/2003.08934',
    hype_score: 85.5,
    trend_label: 'rising' as const,
    current_stars: 5234,
    current_citations: 892,
    days_since_publish: 1200,
  }

  it('renders paper title', () => {
    render(<PaperCard paper={mockPaper} />)
    expect(screen.getByText('Neural Radiance Fields for View Synthesis')).toBeInTheDocument()
  })

  it('renders first 3 authors with et al', () => {
    render(<PaperCard paper={mockPaper} />)
    const authorText = screen.getByText(/Ben Mildenhall/)
    expect(authorText).toBeInTheDocument()
    expect(authorText.textContent).toContain('et al.')
  })

  it('displays hype score', () => {
    render(<PaperCard paper={mockPaper} />)
    expect(screen.getByText(/85\.5/)).toBeInTheDocument()
  })

  it('shows rising trend indicator', () => {
    render(<PaperCard paper={mockPaper} />)
    expect(screen.getByText(/rising|↑/i)).toBeInTheDocument()
  })

  it('displays GitHub stars when available', () => {
    render(<PaperCard paper={mockPaper} />)
    expect(screen.getByText(/5234|5,234/)).toBeInTheDocument()
  })

  it('displays citation count', () => {
    render(<PaperCard paper={mockPaper} />)
    expect(screen.getByText(/892/)).toBeInTheDocument()
  })

  it('renders links to paper sources', () => {
    render(<PaperCard paper={mockPaper} />)
    const links = screen.getAllByRole('link')
    expect(links.length).toBeGreaterThan(0)
  })
})
