import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type { ApiError } from '@/domain/common/types';
import { getStore } from '@/infrastructure/store/storeRef';
import { logout } from '@/infrastructure/store/slices/authSlice';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 60000;

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);

    if (error.response?.status === 401) {
      getStore().dispatch(logout());
    }

    return Promise.reject({
      detail: message,
      status: error.response?.status,
    });
  }
);

export default apiClient;
