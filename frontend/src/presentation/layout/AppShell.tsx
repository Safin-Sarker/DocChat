import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';
import { toast } from 'sonner';
import { TooltipProvider } from '@/presentation/ui/tooltip';
import { Toaster } from '@/presentation/ui/sonner';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainContent } from './MainContent';
import { UploadModal } from '@/presentation/features/documents/UploadModal';
import { useAppSelector, useAppDispatch } from '@/infrastructure/store/hooks';
import { openUploadModal, closeUploadModal } from '@/infrastructure/store/slices/uploadModalSlice';
import { setServerSessionId, clearMessages, addUploadedDocument } from '@/infrastructure/store/slices/chatSlice';
import { healthCheck } from '@/infrastructure/api/health.api';
import { useTheme } from '@/application/theme/useTheme';
import { useDocumentUpload } from '@/application/document/useDocumentUpload';
import { store } from '@/infrastructure/store';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth >= 1024);
  const [isConnected, setIsConnected] = useState(true);
  const [isDragOverlay, setIsDragOverlay] = useState(false);
  const dispatch = useAppDispatch();

  const isUploadModalOpen = useAppSelector((s) => s.uploadModal.isOpen);
  const isUploading = useAppSelector((s) => s.uploadModal.isUploading);

  const {
    mutate: uploadDocument,
    isPending: isGlobalUploading,
  } = useDocumentUpload();

  // Initialize theme
  useTheme();

  // Use ref to track session ID to avoid re-render loops
  const serverSessionIdRef = useRef<string | null>(null);

  // Check server health - skip during uploads to avoid timeout errors
  useEffect(() => {
    serverSessionIdRef.current = store.getState().chat.serverSessionId;

    const checkHealth = async () => {
      // Skip health check if we're uploading a document
      if (store.getState().uploadModal.isUploading) {
        return;
      }

      try {
        const health = await healthCheck();
        setIsConnected(health.status === 'ok' || health.status === 'degraded');

        if (health.session_id) {
          if (serverSessionIdRef.current && serverSessionIdRef.current !== health.session_id) {
            dispatch(clearMessages());
          }
          if (serverSessionIdRef.current !== health.session_id) {
            serverSessionIdRef.current = health.session_id;
            dispatch(setServerSessionId(health.session_id));
          }
        }
      } catch {
        // Only show disconnected if not uploading
        if (!store.getState().uploadModal.isUploading) {
          setIsConnected(false);
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check every 60 seconds
    return () => clearInterval(interval);
  }, [dispatch]);

  const onDropGlobal = useCallback(
    (acceptedFiles: File[], fileRejections: any[]) => {
      setIsDragOverlay(false);

      if (fileRejections.length > 0) {
        toast.error('File not supported', {
          description: 'Please use PDF, DOCX, XLSX, PPTX, TXT, or image files',
        });
        return;
      }

      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        toast.info('Processing document...', {
          description: file.name,
          duration: 5000,
        });

        uploadDocument(file, {
          onSuccess: (response) => {
            dispatch(addUploadedDocument({
              doc_id: response.doc_id,
              filename: file.name,
              pages: response.pages,
              uploadedAt: new Date().toISOString(),
            }));
            toast.success('Document uploaded successfully', {
              description: `${response.pages} pages processed`,
            });
          },
          onError: (error) => {
            toast.error('Upload failed', {
              description: error.message || 'Please try again',
            });
          },
        });
      }
    },
    [uploadDocument, dispatch]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onDropGlobal,
    onDragEnter: () => setIsDragOverlay(true),
    onDragLeave: () => setIsDragOverlay(false),
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/plain': ['.txt'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
    },
    noClick: true,
    noKeyboard: true,
    maxFiles: 1,
    disabled: isUploading || isGlobalUploading,
  });

  const showOverlay = isDragActive || isDragOverlay;

  return (
    <TooltipProvider delayDuration={300}>
      <div {...getRootProps()} className="h-screen flex flex-col bg-background relative">
        <input {...getInputProps()} />

        <Header
          isConnected={isUploading ? true : isConnected} // Show connected during upload
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        <div className="flex-1 flex min-h-0">
          <Sidebar
            isOpen={isSidebarOpen}
            onClose={() => setIsSidebarOpen(false)}
            onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
            onUploadClick={() => dispatch(openUploadModal())}
          />

          <MainContent>{children}</MainContent>
        </div>

        <UploadModal
          open={isUploadModalOpen}
          onOpenChange={(open) => dispatch(open ? openUploadModal() : closeUploadModal())}
        />

        {/* Global drag overlay */}
        {showOverlay && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center pointer-events-none">
            <div className="flex flex-col items-center gap-4 p-8 rounded-2xl border-2 border-dashed border-primary bg-primary/5">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div className="text-center">
                <p className="text-lg font-medium text-foreground">Drop to upload</p>
                <p className="text-sm text-muted-foreground mt-1">PDF, DOCX, XLSX, PPTX, TXT, or image files</p>
              </div>
            </div>
          </div>
        )}

        <Toaster position="bottom-right" />
      </div>
    </TooltipProvider>
  );
}
