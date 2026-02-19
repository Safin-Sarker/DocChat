import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { uploadDocument } from '@/infrastructure/api/document.api';
import type { DocumentUploadResponse } from '@/domain/document/types';

export const useDocumentUpload = () => {
  const [uploadProgress, setUploadProgress] = useState(0);

  const mutation = useMutation<DocumentUploadResponse, Error, File>({
    mutationFn: (file: File) =>
      uploadDocument(file, (progressEvent) => {
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
