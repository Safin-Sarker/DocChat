import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type { ApiError } from '@/domain/common/types';
import { useAuthStore } from '@/infrastructure/stores/authStore';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 30000;

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
    const token = useAuthStore.getState().token;
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
      useAuthStore.getState().logout();
    }

    return Promise.reject({
      detail: message,
      status: error.response?.status,
    });
  }
);

export default apiClient;
