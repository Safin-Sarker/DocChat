import { useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useDocumentUpload } from '@/hooks/useUpload';
import { useChatStore } from '@/stores/chatStore';
import { useUploadModal } from '@/hooks/useUploadModal';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface UploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadModal({ open, onOpenChange }: UploadModalProps) {
  const {
    mutate: uploadDocument,
    isPending,
    isSuccess,
    isError,
    data,
    error,
    uploadProgress,
    reset,
  } = useDocumentUpload();

  const setCurrentDoc = useChatStore((state) => state.setCurrentDoc);
  const addUploadedDocument = useChatStore((state) => state.addUploadedDocument);
  const { setUploading } = useUploadModal();

  // Track if we've shown the toast to prevent duplicates
  const hasShownSuccessToast = useRef(false);
  const hasShownErrorToast = useRef(false);

  // Update uploading state
  useEffect(() => {
    setUploading(isPending);
  }, [isPending, setUploading]);

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      reset();
      hasShownSuccessToast.current = false;
      hasShownErrorToast.current = false;
    }
  }, [open, reset]);

  // Auto-close on success
  useEffect(() => {
    if (isSuccess && data && !hasShownSuccessToast.current) {
      hasShownSuccessToast.current = true;
      toast.success('Document uploaded successfully', {
        description: `${data.pages} pages processed`,
      });
      const timer = setTimeout(() => {
        onOpenChange(false);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [isSuccess, data, onOpenChange]);

  // Show error toast
  useEffect(() => {
    if (isError && !hasShownErrorToast.current) {
      hasShownErrorToast.current = true;
      toast.error('Upload failed', {
        description: error?.message || 'Please try again with a different file',
      });
    }
  }, [isError, error]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        // Reset toast flags when starting a new upload
        hasShownSuccessToast.current = false;
        hasShownErrorToast.current = false;

        toast.info('Processing document...', {
          description: 'Large documents may take several minutes',
          duration: 5000,
        });

        uploadDocument(file, {
          onSuccess: (response) => {
            setCurrentDoc(response.doc_id);
            addUploadedDocument({
              doc_id: response.doc_id,
              filename: file.name,
              pages: response.pages,
              uploadedAt: new Date().toISOString(),
            });
          },
        });
      }
    },
    [uploadDocument, setCurrentDoc, addUploadedDocument]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
    },
    maxFiles: 1,
    disabled: isPending,
  });

  const handleRetry = () => {
    hasShownSuccessToast.current = false;
    hasShownErrorToast.current = false;
    reset();
  };

  return (
    <Dialog open={open} onOpenChange={isPending ? undefined : onOpenChange}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={isPending ? (e) => e.preventDefault() : undefined}>
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Upload a PDF, DOCX, or image file to start chatting
          </DialogDescription>
        </DialogHeader>

        <div
          {...getRootProps()}
          className={cn(
            'relative mt-4 rounded-lg border-2 border-dashed transition-all duration-200',
            isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50 hover:bg-accent/50',
            isPending && 'cursor-not-allowed opacity-70',
            !isPending && !isSuccess && !isError && 'cursor-pointer'
          )}
        >
          <input {...getInputProps()} />

          <div className="flex flex-col items-center justify-center p-8 text-center">
            {isPending ? (
              <>
                <div className="relative mb-4">
                  <Loader2 className="h-12 w-12 text-primary animate-spin" />
                </div>
                <div className="w-full space-y-2">
                  <Progress value={uploadProgress} className="h-1.5" />
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Processing...</span>
                    <span className="font-medium text-primary">{uploadProgress}%</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Large documents may take several minutes
                  </p>
                </div>
              </>
            ) : isSuccess && data ? (
              <>
                <CheckCircle2 className="h-12 w-12 text-green-500 mb-4" />
                <p className="font-medium text-green-600 mb-2">Upload Successful!</p>
                <div className="flex gap-4 text-sm text-muted-foreground">
                  <span>{data.pages} pages</span>
                  <span>{data.upserted_vectors} vectors</span>
                </div>
              </>
            ) : isError ? (
              <>
                <XCircle className="h-12 w-12 text-destructive mb-4" />
                <p className="font-medium text-destructive mb-2">Upload Failed</p>
                <p className="text-sm text-muted-foreground mb-4">
                  {error?.message || 'Please try again'}
                </p>
                <Button variant="outline" size="sm" onClick={handleRetry}>
                  Try Again
                </Button>
              </>
            ) : (
              <>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                  <Upload className="h-6 w-6 text-primary" />
                </div>
                <p className="font-medium text-foreground mb-1">
                  {isDragActive ? 'Drop your file here' : 'Drag & drop a file'}
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  or click to browse
                </p>
                <div className="flex gap-2">
                  <Badge variant="secondary" className="text-xs">
                    <FileText className="mr-1 h-3 w-3" />
                    PDF
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    <FileText className="mr-1 h-3 w-3" />
                    DOCX
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    Images
                  </Badge>
                </div>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
