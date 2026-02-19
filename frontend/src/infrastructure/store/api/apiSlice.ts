import { createApi, type BaseQueryFn } from '@reduxjs/toolkit/query/react';
import type { AxiosError, AxiosRequestConfig } from 'axios';
import apiClient from '@/infrastructure/api/apiClient';
import type { ApiError } from '@/domain/common/types';
import type { LoginRequest, RegisterRequest, AuthResponse } from '@/domain/auth/types';
import type { DocumentUploadResponse, UploadedDocument, DeleteDocumentResponse } from '@/domain/document/types';
import type { QueryRequest, QueryResponse } from '@/domain/query/types';
import type { GraphQueryResponse } from '@/domain/graph/types';
import type { HealthCheckResponse } from '@/domain/health/types';

const axiosBaseQuery: BaseQueryFn<
  { url: string; method?: AxiosRequestConfig['method']; data?: unknown; params?: unknown; headers?: Record<string, string>; timeout?: number; responseType?: AxiosRequestConfig['responseType']; onUploadProgress?: AxiosRequestConfig['onUploadProgress'] },
  unknown,
  ApiError
> = async ({ url, method = 'GET', data, params, headers, timeout, responseType, onUploadProgress }) => {
  try {
    const result = await apiClient({
      url,
      method,
      data,
      params,
      headers,
      timeout,
      responseType,
      onUploadProgress,
    });
    return { data: result.data };
  } catch (err) {
    const axiosError = err as AxiosError<ApiError>;
    return {
      error: {
        detail: axiosError.response?.data?.detail || axiosError.message || 'An error occurred',
        status: axiosError.response?.status,
      },
    };
  }
};

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: axiosBaseQuery,
  tagTypes: ['Documents'],
  endpoints: (builder) => ({
    login: builder.mutation<AuthResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/api/v1/auth/login',
        method: 'POST',
        data: credentials,
      }),
    }),

    register: builder.mutation<AuthResponse, RegisterRequest>({
      query: (data) => ({
        url: '/api/v1/auth/register',
        method: 'POST',
        data,
      }),
    }),

    getDocuments: builder.query<UploadedDocument[], void>({
      query: () => ({ url: '/api/v1/documents/' }),
      providesTags: ['Documents'],
    }),

    uploadDocument: builder.mutation<
      DocumentUploadResponse,
      { file: File; onUploadProgress?: AxiosRequestConfig['onUploadProgress'] }
    >({
      queryFn: async ({ file, onUploadProgress }, _api, _extraOptions, baseQuery) => {
        const formData = new FormData();
        formData.append('file', file);
        const result = await baseQuery({
          url: '/api/v1/documents/upload',
          method: 'POST',
          data: formData,
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 1800000,
          onUploadProgress,
        });
        if (result.error) return { error: result.error as ApiError };
        return { data: result.data as DocumentUploadResponse };
      },
      invalidatesTags: ['Documents'],
    }),

    deleteDocument: builder.mutation<DeleteDocumentResponse, string>({
      query: (docId) => ({
        url: `/api/v1/documents/${docId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Documents'],
    }),

    getDocumentFile: builder.query<Blob, string>({
      queryFn: async (docId, _api, _extraOptions, baseQuery) => {
        const result = await baseQuery({
          url: `/api/v1/documents/${docId}/file`,
          responseType: 'blob',
        });
        if (result.error) return { error: result.error as ApiError };
        return { data: result.data as Blob };
      },
    }),

    queryRAG: builder.mutation<QueryResponse, QueryRequest>({
      query: (queryRequest) => ({
        url: '/api/v1/query/',
        method: 'POST',
        data: queryRequest,
      }),
    }),

    getRelatedEntities: builder.query<GraphQueryResponse, { entities: string[]; max_depth?: number; limit?: number }>({
      query: (graphRequest) => ({
        url: '/api/v1/graph/related',
        method: 'POST',
        data: graphRequest,
      }),
      keepUnusedDataFor: 300,
    }),

    healthCheck: builder.query<HealthCheckResponse, void>({
      query: () => ({ url: '/health' }),
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useGetDocumentsQuery,
  useUploadDocumentMutation,
  useDeleteDocumentMutation,
  useGetDocumentFileQuery,
  useQueryRAGMutation,
  useGetRelatedEntitiesQuery,
  useHealthCheckQuery,
} = apiSlice;
