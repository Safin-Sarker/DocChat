import { useState, useEffect, useRef, type ReactNode } from 'react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Toaster } from '@/components/ui/sonner';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainContent } from './MainContent';
import { UploadModal } from '@/components/features/documents/UploadModal';
import { useChatStore } from '@/stores/chatStore';
import { useUploadModal } from '@/hooks/useUploadModal';
import { api } from '@/api/client';
import { useTheme } from '@/hooks/useTheme';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(true);

  const { isOpen: isUploadModalOpen, isUploading, open: openUploadModal, close: closeUploadModal } = useUploadModal();

  // Initialize theme
  useTheme();

  // Use ref to track session ID to avoid re-render loops
  const serverSessionIdRef = useRef<string | null>(null);

  // Check server health - skip during uploads to avoid timeout errors
  useEffect(() => {
    const { serverSessionId, setServerSessionId, clearMessages } = useChatStore.getState();
    serverSessionIdRef.current = serverSessionId;

    const checkHealth = async () => {
      // Skip health check if we're uploading a document
      if (useUploadModal.getState().isUploading) {
        return;
      }

      try {
        const health = await api.healthCheck();
        setIsConnected(health.status === 'ok');

        if (health.session_id) {
          if (serverSessionIdRef.current && serverSessionIdRef.current !== health.session_id) {
            clearMessages();
          }
          if (serverSessionIdRef.current !== health.session_id) {
            serverSessionIdRef.current = health.session_id;
            setServerSessionId(health.session_id);
          }
        }
      } catch {
        // Only show disconnected if not uploading
        if (!useUploadModal.getState().isUploading) {
          setIsConnected(false);
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check every 60 seconds
    return () => clearInterval(interval);
  }, []);

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
            onUploadClick={openUploadModal}
          />

          <MainContent>{children}</MainContent>
        </div>

        <UploadModal
          open={isUploadModalOpen}
          onOpenChange={(open) => open ? openUploadModal() : closeUploadModal()}
        />

        <Toaster position="bottom-right" />
      </div>
    </TooltipProvider>
  );
}
