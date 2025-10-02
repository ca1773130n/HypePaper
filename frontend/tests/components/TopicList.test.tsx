import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TopicList from '../../src/components/TopicList'

describe('TopicList', () => {
  const mockTopics = [
    {
      id: '1',
      name: 'neural rendering',
      description: 'Novel view synthesis using neural networks',
      paper_count: 247,
      created_at: '2025-01-01T00:00:00Z',
    },
    {
      id: '2',
      name: 'diffusion models',
      description: 'Generative models using diffusion processes',
      paper_count: 512,
      created_at: '2025-01-01T00:00:00Z',
    },
  ]

  it('renders list of topics', () => {
    const onAdd = vi.fn()
    render(<TopicList topics={mockTopics} onAddTopic={onAdd} watchedTopics={[]} />)

    expect(screen.getByText('neural rendering')).toBeInTheDocument()
    expect(screen.getByText('diffusion models')).toBeInTheDocument()
  })

  it('displays paper count for each topic', () => {
    const onAdd = vi.fn()
    render(<TopicList topics={mockTopics} onAddTopic={onAdd} watchedTopics={[]} />)

    expect(screen.getByText(/247/)).toBeInTheDocument()
    expect(screen.getByText(/512/)).toBeInTheDocument()
  })

  it('shows add button for unwatched topics', () => {
    const onAdd = vi.fn()
    render(<TopicList topics={mockTopics} onAddTopic={onAdd} watchedTopics={[]} />)

    const addButtons = screen.getAllByRole('button', { name: /add/i })
    expect(addButtons.length).toBe(2)
  })

  it('calls onAddTopic when add button clicked', () => {
    const onAdd = vi.fn()
    render(<TopicList topics={mockTopics} onAddTopic={onAdd} watchedTopics={[]} />)

    const addButtons = screen.getAllByRole('button', { name: /add/i })
    fireEvent.click(addButtons[0])

    expect(onAdd).toHaveBeenCalledWith('1')
  })

  it('disables add button for already watched topics', () => {
    const onAdd = vi.fn()
    render(<TopicList topics={mockTopics} onAddTopic={onAdd} watchedTopics={['1']} />)

    const buttons = screen.getAllByRole('button')
    // First button should be disabled or show "watching"
    expect(buttons[0]).toHaveAttribute('disabled', '')
  })
})
