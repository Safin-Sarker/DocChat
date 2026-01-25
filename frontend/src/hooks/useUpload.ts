import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api/client';
import type { DocumentUploadResponse } from '../types/api';

export const useDocumentUpload = () => {
  const [uploadProgress, setUploadProgress] = useState(0);

  const mutation = useMutation<DocumentUploadResponse, Error, File>({
    mutationFn: (file: File) =>
      api.uploadDocument(file, (progressEvent) => {
        const progress = progressEvent.total
          ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
          : 0;
        setUploadProgress(progress);
      }),
    onSuccess: () => {
      setUploadProgress(0);
    },
    onError: () => {
      setUploadProgress(0);
    },
  });

  return {
    ...mutation,
    uploadProgress,
  };
};
