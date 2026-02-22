import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FileText } from 'lucide-react'
import { EmptyState } from '../EmptyState'

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(
      <EmptyState
        icon={FileText}
        title="No items found"
        description="Try uploading something"
      />
    )
    expect(screen.getByText('No items found')).toBeInTheDocument()
    expect(screen.getByText('Try uploading something')).toBeInTheDocument()
  })

  it('renders the provided icon', () => {
    const { container } = render(
      <EmptyState
        icon={FileText}
        title="Empty"
        description="Nothing here"
      />
    )
    // Lucide renders an SVG element
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})
