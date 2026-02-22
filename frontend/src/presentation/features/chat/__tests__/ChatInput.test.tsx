import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInput } from '../ChatInput'

describe('ChatInput', () => {
  it('renders with placeholder', () => {
    render(<ChatInput onSubmit={vi.fn()} />)
    expect(screen.getByPlaceholderText('Ask about your document...')).toBeInTheDocument()
  })

  it('calls onSubmit with trimmed text on Enter and clears input', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn()
    render(<ChatInput onSubmit={handleSubmit} />)

    const textarea = screen.getByPlaceholderText('Ask about your document...')
    await user.type(textarea, '  hello world  ')
    await user.keyboard('{Enter}')

    expect(handleSubmit).toHaveBeenCalledWith('hello world')
    expect(textarea).toHaveValue('')
  })

  it('does not submit on Shift+Enter', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn()
    render(<ChatInput onSubmit={handleSubmit} />)

    const textarea = screen.getByPlaceholderText('Ask about your document...')
    await user.type(textarea, 'line one')
    await user.keyboard('{Shift>}{Enter}{/Shift}')

    expect(handleSubmit).not.toHaveBeenCalled()
  })

  it('disables input and button when disabled prop is true', () => {
    render(<ChatInput onSubmit={vi.fn()} disabled />)
    const textarea = screen.getByPlaceholderText('Select a document to start chatting...')
    expect(textarea).toBeDisabled()
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('does not submit empty or whitespace-only input', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn()
    render(<ChatInput onSubmit={handleSubmit} />)

    const textarea = screen.getByPlaceholderText('Ask about your document...')
    await user.type(textarea, '   ')
    await user.keyboard('{Enter}')

    expect(handleSubmit).not.toHaveBeenCalled()
  })
})
