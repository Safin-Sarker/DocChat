import { describe, it, expect } from 'vitest'
import authReducer, { setAuth, setTokens, logout } from '../slices/authSlice'

describe('authSlice', () => {
  it('has correct initial state', () => {
    const state = authReducer(undefined, { type: '@@INIT' })
    expect(state.token).toBeNull()
    expect(state.refreshToken).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('setAuth sets token, refreshToken, user, and isAuthenticated', () => {
    const user = { user_id: 'u1', email: 'a@b.com', username: 'alice' }
    const state = authReducer(undefined, setAuth({ token: 'tok123', refreshToken: 'ref123', user }))
    expect(state.token).toBe('tok123')
    expect(state.refreshToken).toBe('ref123')
    expect(state.user).toEqual(user)
    expect(state.isAuthenticated).toBe(true)
  })

  it('setTokens updates only tokens without changing user', () => {
    const user = { user_id: 'u1', email: 'a@b.com', username: 'alice' }
    const authedState = authReducer(undefined, setAuth({ token: 'old', refreshToken: 'oldref', user }))
    const state = authReducer(authedState, setTokens({ token: 'new', refreshToken: 'newref' }))
    expect(state.token).toBe('new')
    expect(state.refreshToken).toBe('newref')
    expect(state.user).toEqual(user)
    expect(state.isAuthenticated).toBe(true)
  })

  it('logout resets to initial state including refreshToken', () => {
    const user = { user_id: 'u1', email: 'a@b.com', username: 'alice' }
    const authedState = authReducer(undefined, setAuth({ token: 'tok', refreshToken: 'ref', user }))
    const state = authReducer(authedState, logout())
    expect(state.token).toBeNull()
    expect(state.refreshToken).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
