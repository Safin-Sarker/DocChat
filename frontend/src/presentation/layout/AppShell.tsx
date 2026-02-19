import { useState, useEffect, useRef, type ReactNode } from 'react';
import { TooltipProvider } from '@/presentation/ui/tooltip';
import { Toaster } from '@/presentation/ui/sonner';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainContent } from './MainContent';
import { UploadModal } from '@/presentation/features/documents/UploadModal';
import { useAppSelector, useAppDispatch } from '@/infrastructure/store/hooks';
import { openUploadModal, closeUploadModal } from '@/infrastructure/store/slices/uploadModalSlice';
import { setServerSessionId, clearMessages } from '@/infrastructure/store/slices/chatSlice';
import { healthCheck } from '@/infrastructure/api/health.api';
import { useTheme } from '@/application/theme/useTheme';
import { store } from '@/infrastructure/store';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth >= 1024);
  const [isConnected, setIsConnected] = useState(true);
  const dispatch = useAppDispatch();

  const isUploadModalOpen = useAppSelector((s) => s.uploadModal.isOpen);
  const isUploading = useAppSelector((s) => s.uploadModal.isUploading);

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
        setIsConnected(health.status === 'ok');

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

  return (
    <TooltipProvider delayDuration={300}>
      <div className="h-screen flex flex-col bg-background">
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

        <Toaster position="bottom-right" />
      </div>
    </TooltipProvider>
  );
}
