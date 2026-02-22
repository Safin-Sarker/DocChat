import { describe, it, expect } from 'vitest'
import authReducer, { setAuth, logout } from '../slices/authSlice'

describe('authSlice', () => {
  it('has correct initial state', () => {
    const state = authReducer(undefined, { type: '@@INIT' })
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('setAuth sets token, user, and isAuthenticated', () => {
    const user = { user_id: 'u1', email: 'a@b.com', username: 'alice' }
    const state = authReducer(undefined, setAuth({ token: 'tok123', user }))
    expect(state.token).toBe('tok123')
    expect(state.user).toEqual(user)
    expect(state.isAuthenticated).toBe(true)
  })

  it('logout resets to initial state', () => {
    const user = { user_id: 'u1', email: 'a@b.com', username: 'alice' }
    const authedState = authReducer(undefined, setAuth({ token: 'tok', user }))
    const state = authReducer(authedState, logout())
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
