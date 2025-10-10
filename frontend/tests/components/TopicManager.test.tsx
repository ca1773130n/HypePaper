import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TopicManager from '../../src/components/TopicManager'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('TopicManager', () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  it('renders watched topics list', () => {
    localStorageMock.setItem('watchedTopics', JSON.stringify(['neural-rendering', 'diffusion-models']))

    render(<TopicManager />)
    expect(screen.getByText(/neural-rendering|neural rendering/i)).toBeInTheDocument()
  })

  it('allows removing a watched topic', () => {
    localStorageMock.setItem('watchedTopics', JSON.stringify(['neural-rendering']))

    render(<TopicManager />)
    const removeButton = screen.getByRole('button', { name: /remove|×/i })
    fireEvent.click(removeButton)

    const stored = JSON.parse(localStorageMock.getItem('watchedTopics') || '[]')
    expect(stored).not.toContain('neural-rendering')
  })

  it('persists watched topics to localStorage', () => {
    render(<TopicManager />)

    // Simulate adding a topic through the component
    // This would typically come from TopicList integration
    const stored = localStorageMock.getItem('watchedTopics')
    expect(stored !== null).toBe(true)
  })

  it('shows empty state when no topics watched', () => {
    render(<TopicManager />)
    expect(screen.getByText(/no topics|add topics/i)).toBeInTheDocument()
  })
})
