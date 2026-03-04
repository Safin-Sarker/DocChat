import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from '@/domain/common/types';
import { getStore } from '@/infrastructure/store/storeRef';
import { logout, setTokens } from '@/infrastructure/store/slices/authSlice';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 60000;

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Refresh token queue ---

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token!);
    }
  });
  failedQueue = [];
}

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = getStore().getState().auth.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor with transparent refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Only attempt refresh on 401, not for auth endpoints, and not if already retried
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register')
    ) {
      const store = getStore();
      const refreshToken = store.getState().auth.refreshToken;

      if (!refreshToken) {
        store.dispatch(logout());
        return Promise.reject({
          detail: 'Session expired. Please log in again.',
          status: 401,
        });
      }

      if (isRefreshing) {
        // Queue this request until the ongoing refresh completes
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          originalRequest._retry = true;
          return apiClient(originalRequest);
        });
      }

      isRefreshing = true;
      originalRequest._retry = true;

      try {
        // Use raw axios to avoid interceptor recursion
        const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: newRefreshToken } = response.data;

        store.dispatch(setTokens({ token: access_token, refreshToken: newRefreshToken }));

        processQueue(null, access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        store.dispatch(logout());
        return Promise.reject({
          detail: 'Session expired. Please log in again.',
          status: 401,
        });
      } finally {
        isRefreshing = false;
      }
    }

    // Non-401 errors or unrecoverable 401s
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);

    return Promise.reject({
      detail: message,
      status: error.response?.status,
    });
  }
);

export default apiClient;
