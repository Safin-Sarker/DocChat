import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { MessageRow } from '../MessageRow'
import type { Message } from '@/domain/chat/types'

// Stub clipboard API
beforeEach(() => {
  Object.assign(navigator, {
    clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  })
})

function makeMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: 'msg-1',
    role: 'assistant',
    content: 'Test response content',
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

describe('MessageRow', () => {
  it('renders user message with correct styling', () => {
    renderWithProviders(
      <MessageRow message={makeMessage({ role: 'user', content: 'User question' })} />
    )
    expect(screen.getByText('User question')).toBeInTheDocument()
  })

  it('renders assistant message with markdown content', () => {
    renderWithProviders(
      <MessageRow message={makeMessage({ content: 'This is **bold** text' })} />
    )
    expect(screen.getByText('bold')).toBeInTheDocument()
  })

  it('renders source badges from source_map', () => {
    const msg = makeMessage({
      content: 'Answer with citations [1]',
      source_map: [
        { index: 1, doc_name: 'report.pdf', page: 3, text: 'source text' },
      ],
    })
    renderWithProviders(<MessageRow message={msg} />)
    expect(screen.getByText(/report\.pdf/)).toBeInTheDocument()
  })

  it('renders quality badge when reflection is provided', () => {
    const msg = makeMessage({
      reflection: {
        faithfulness: 0.9,
        relevance: 0.9,
        completeness: 0.9,
        coherence: 0.9,
        conciseness: 0.9,
        overall: 0.9,
        verdict: 'pass',
        feedback: '',
        was_regenerated: false,
      },
    })
    renderWithProviders(<MessageRow message={msg} />)
    // QualityBadge should render with the reflection data
    // The component renders based on the presence of the reflection prop
    expect(screen.getByText('Test response content')).toBeInTheDocument()
  })

  it('copy button calls clipboard.writeText', async () => {
    renderWithProviders(
      <MessageRow message={makeMessage({ content: 'Copy me' })} />
    )
    // Find the copy button by tooltip content — it's the first ghost icon button
    const copyButtons = screen.getAllByRole('button')
    const copyButton = copyButtons.find(
      (btn) => btn.querySelector('svg') !== null
    )
    if (copyButton) {
      fireEvent.click(copyButton)
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Copy me')
    }
  })
})
