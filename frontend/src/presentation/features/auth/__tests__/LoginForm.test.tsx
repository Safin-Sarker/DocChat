import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/test-utils'
import { LoginForm } from '../LoginForm'

// Mock the auth API to avoid real network calls
vi.mock('@/infrastructure/api/auth.api', () => ({
  login: vi.fn(),
  register: vi.fn(),
}))

describe('LoginForm', () => {
  it('renders login tab by default with email/password fields', () => {
    renderWithProviders(<LoginForm />, { route: '/login' })
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument()
  })

  it('switches to register tab when Create Account is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />, { route: '/login' })
    await user.click(screen.getByRole('tab', { name: 'Create Account' }))
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
  })

  it('shows password mismatch error on register', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />, { route: '/login' })
    await user.click(screen.getByRole('tab', { name: 'Create Account' }))

    await user.type(screen.getByLabelText('Email'), 'test@example.com')
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.type(screen.getByLabelText('Confirm Password'), 'different')
    await user.click(screen.getByRole('button', { name: 'Create Account' }))

    expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
  })

  it('shows short password error on register', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />, { route: '/login' })
    await user.click(screen.getByRole('tab', { name: 'Create Account' }))

    await user.type(screen.getByLabelText('Email'), 'test@example.com')
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), '12345')
    await user.type(screen.getByLabelText('Confirm Password'), '12345')
    await user.click(screen.getByRole('button', { name: 'Create Account' }))

    expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument()
  })
})
