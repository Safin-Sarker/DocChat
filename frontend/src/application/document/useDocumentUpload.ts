import { useState, useCallback } from 'react';
import { useUploadDocumentMutation } from '@/infrastructure/store/api/apiSlice';
import type { DocumentUploadResponse } from '@/domain/document/types';
import type { AxiosRequestConfig } from 'axios';

export const useDocumentUpload = () => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isReset, setIsReset] = useState(false);
  const [trigger, result] = useUploadDocumentMutation();

  const mutate = useCallback(
    (
      file: File,
      options?: {
        onSuccess?: (data: DocumentUploadResponse) => void;
        onError?: (error: Error) => void;
      }
    ) => {
      setIsReset(false);
      setUploadProgress(0);

      trigger({
        file,
        onUploadProgress: ((progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        }) as AxiosRequestConfig['onUploadProgress'],
      })
        .unwrap()
        .then((data) => {
          setUploadProgress(0);
          options?.onSuccess?.(data);
        })
        .catch((err) => {
          setUploadProgress(0);
          options?.onError?.(err instanceof Error ? err : new Error(err?.detail || 'Upload failed'));
        });
    },
    [trigger]
  );

  const reset = useCallback(() => {
    setIsReset(true);
    setUploadProgress(0);
    result.reset();
  }, [result]);

  return {
    mutate,
    isPending: result.isLoading,
    isSuccess: result.isSuccess && !isReset,
    isError: result.isError && !isReset,
    data: result.data,
    error: result.error ? new Error((result.error as { detail?: string })?.detail || 'Upload failed') : null,
    uploadProgress,
    reset,
  };
};
