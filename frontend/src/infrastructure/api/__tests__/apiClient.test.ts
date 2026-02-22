import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

// Mock the store reference module
const mockGetState = vi.fn()
const mockDispatch = vi.fn()

vi.mock('@/infrastructure/store/storeRef', () => ({
  getStore: () => ({
    getState: mockGetState,
    dispatch: mockDispatch,
  }),
}))

vi.mock('@/infrastructure/store/slices/authSlice', () => ({
  logout: () => ({ type: 'auth/logout' }),
}))

describe('apiClient interceptors', () => {
  let requestInterceptor: (config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig
  let responseErrorInterceptor: (error: any) => Promise<never>

  beforeEach(async () => {
    vi.resetModules()
    mockGetState.mockReturnValue({
      auth: { token: 'test-jwt-token', user: null, isAuthenticated: true },
    })

    // Spy on interceptors to capture the handler functions
    const useRequestSpy = vi.fn()
    const useResponseSpy = vi.fn()

    vi.spyOn(axios, 'create').mockReturnValue({
      interceptors: {
        request: { use: useRequestSpy },
        response: { use: useResponseSpy },
      },
      defaults: { headers: { common: {} } },
    } as unknown as AxiosInstance)

    // Re-import to trigger interceptor registration
    await import('../apiClient')

    requestInterceptor = useRequestSpy.mock.calls[0][0]
    responseErrorInterceptor = useResponseSpy.mock.calls[0][1]
  })

  it('adds auth header from store', () => {
    const config = { headers: {} } as InternalAxiosRequestConfig
    const result = requestInterceptor(config)
    expect(result.headers.Authorization).toBe('Bearer test-jwt-token')
  })

  it('handles 401 by dispatching logout', async () => {
    const error = {
      response: { status: 401, data: { detail: 'Unauthorized' } },
      message: 'Request failed',
    }
    await expect(responseErrorInterceptor(error)).rejects.toEqual({
      detail: 'Unauthorized',
      status: 401,
    })
    expect(mockDispatch).toHaveBeenCalledWith({ type: 'auth/logout' })
  })

  it('formats error response with detail', async () => {
    const error = {
      response: { status: 500, data: { detail: 'Server error' } },
      message: 'Request failed',
    }
    await expect(responseErrorInterceptor(error)).rejects.toEqual({
      detail: 'Server error',
      status: 500,
    })
  })
})
