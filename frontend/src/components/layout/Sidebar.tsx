import { useState, useEffect, useRef } from 'react';
import { Plus, Upload, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { UserMenu } from '@/components/shared/UserMenu';
import { DocumentList } from '@/components/features/documents/DocumentList';
import { useChatStore } from '@/stores/chatStore';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/api/client';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadClick: () => void;
}

export function Sidebar({ isOpen, onClose, onUploadClick }: SidebarProps) {
  const [isLoading, setIsLoading] = useState(false);
  const hasFetched = useRef(false);
  const { isAuthenticated } = useAuthStore();
  const { clearMessages, setCurrentDoc } = useChatStore();

  // Fetch documents only once on mount
  useEffect(() => {
    if (!isAuthenticated || hasFetched.current) return;

    const fetchDocuments = async () => {
      hasFetched.current = true;
      setIsLoading(true);
      try {
        const docs = await api.getDocuments();
        useChatStore.getState().setUploadedDocuments(docs);
      } catch (error) {
        console.error('Failed to fetch documents:', error);
        hasFetched.current = false; // Allow retry on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, [isAuthenticated]);

  const handleNewChat = () => {
    clearMessages();
    setCurrentDoc(null);
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-[260px] bg-background border-r flex flex-col transition-transform duration-300 ease-in-out lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Mobile close button */}
        <div className="flex items-center justify-between p-4 lg:hidden">
          <span className="font-semibold">Menu</span>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Action buttons */}
        <div className="p-3 space-y-2">
          <Button
            variant="outline"
            className="w-full justify-start gap-2"
            onClick={handleNewChat}
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
          <Button
            variant="default"
            className="w-full justify-start gap-2"
            onClick={() => {
              onUploadClick();
              onClose();
            }}
          >
            <Upload className="h-4 w-4" />
            Upload Document
          </Button>
        </div>

        <Separator />

        {/* Documents section */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="px-3 py-2">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Documents
            </h3>
          </div>
          <ScrollArea className="flex-1 px-2">
            <DocumentList isLoading={isLoading} />
          </ScrollArea>
        </div>

        <Separator />

        {/* User section */}
        <div className="p-3">
          <UserMenu />
        </div>
      </aside>
    </>
  );
}
