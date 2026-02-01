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
} from '../types/api';

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

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject({
      detail: message,
      status: error.response?.status,
    });
  }
);

// API functions
export const api = {
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

  // Delete document
  deleteDocument: async (docId: string): Promise<DeleteDocumentResponse> => {
    const response = await apiClient.delete<DeleteDocumentResponse>(
      `/api/v1/documents/${docId}`
    );
    return response.data;
  },
};

export default apiClient;
