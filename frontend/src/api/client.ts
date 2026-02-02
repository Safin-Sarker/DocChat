import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  DocumentUploadResponse,
  DeleteDocumentResponse,
  GraphQueryRequest,
  GraphQueryResponse,
  HealthCheckResponse,
  ApiError,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  UploadedDocument,
} from '../types/api';
import { useAuthStore } from '../stores/authStore';

// Create axios instance with default config
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
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

    // Handle 401 errors - logout user
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }

    return Promise.reject({
      detail: message,
      status: error.response?.status,
    });
  }
);

// API functions
export const api = {
  // Auth
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data);
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await apiClient.get<HealthCheckResponse>('/health');
    return response.data;
  },

  // Document upload
  uploadDocument: async (file: File, onUploadProgress?: (progressEvent: any) => void): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DocumentUploadResponse>(
      '/api/v1/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
        timeout: 300000, // 5 minutes for document processing
      }
    );
    return response.data;
  },

  // Query RAG
  queryRAG: async (queryRequest: QueryRequest): Promise<QueryResponse> => {
    const response = await apiClient.post<QueryResponse>(
      '/api/v1/query/',
      queryRequest
    );
    return response.data;
  },

  // Get related entities from graph
  getRelatedEntities: async (graphRequest: GraphQueryRequest): Promise<GraphQueryResponse> => {
    const response = await apiClient.post<GraphQueryResponse>(
      '/api/v1/graph/related',
      graphRequest
    );
    return response.data;
  },

  // Get user's documents
  getDocuments: async (): Promise<UploadedDocument[]> => {
    const response = await apiClient.get<UploadedDocument[]>('/api/v1/documents/');
    return response.data;
  },

  // Delete document
  deleteDocument: async (docId: string): Promise<DeleteDocumentResponse> => {
    const response = await apiClient.delete<DeleteDocumentResponse>(
      `/api/v1/documents/${docId}`
    );
    return response.data;
  },
};

export default apiClient;
