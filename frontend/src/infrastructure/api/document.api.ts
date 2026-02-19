import apiClient from './apiClient';
import type { DocumentUploadResponse, UploadedDocument, DeleteDocumentResponse } from '@/domain/document/types';

export const uploadDocument = async (file: File, onUploadProgress?: (progressEvent: any) => void): Promise<DocumentUploadResponse> => {
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
      timeout: 1800000, // 30 minutes for large document processing
    }
  );
  return response.data;
};

export const getDocuments = async (): Promise<UploadedDocument[]> => {
  const response = await apiClient.get<UploadedDocument[]>('/api/v1/documents/');
  return response.data;
};

export const deleteDocument = async (docId: string): Promise<DeleteDocumentResponse> => {
  const response = await apiClient.delete<DeleteDocumentResponse>(
    `/api/v1/documents/${docId}`
  );
  return response.data;
};

export const getDocumentFile = async (docId: string): Promise<Blob> => {
  const response = await apiClient.get(
    `/api/v1/documents/${docId}/file`,
    {
      responseType: 'blob',
    }
  );
  return response.data as Blob;
};
