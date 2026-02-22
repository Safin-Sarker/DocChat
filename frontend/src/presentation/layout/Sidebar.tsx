import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Plus, Upload, PanelLeftClose, Activity } from 'lucide-react';
import { Button } from '@/presentation/ui/button';
import { ScrollArea } from '@/presentation/ui/scroll-area';
import { UserMenu } from '@/presentation/shared/UserMenu';
import { DocumentList } from '@/presentation/features/documents/DocumentList';
import { useAppSelector, useAppDispatch } from '@/infrastructure/store/hooks';
import { clearMessages, clearDocSelection, setUploadedDocuments } from '@/infrastructure/store/slices/chatSlice';
import { getDocuments } from '@/infrastructure/api/document.api';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onToggleSidebar: () => void;
  onUploadClick: () => void;
}

export function Sidebar({ isOpen, onClose, onToggleSidebar, onUploadClick }: SidebarProps) {
  const [isLoading, setIsLoading] = useState(false);
  const hasFetched = useRef(false);
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const uploadedDocuments = useAppSelector((s) => s.chat.uploadedDocuments);
  const dispatch = useAppDispatch();

  // Fetch documents only once on mount
  useEffect(() => {
    if (!isAuthenticated || hasFetched.current) return;

    const fetchDocuments = async () => {
      hasFetched.current = true;
      setIsLoading(true);
      try {
        const docs = await getDocuments();
        dispatch(setUploadedDocuments(docs));
      } catch (error) {
        console.error('Failed to fetch documents:', error);
        hasFetched.current = false; // Allow retry on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, [isAuthenticated, dispatch]);

  const handleNewChat = () => {
    dispatch(clearMessages());
    dispatch(clearDocSelection());
  };

  const docCount = uploadedDocuments.length;

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
          'fixed inset-y-0 left-0 z-50 w-[260px] bg-muted/30 border-r border-border/50 flex flex-col transition-transform duration-300 ease-in-out lg:static',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:hidden'
        )}
      >
        {/* Top row: collapse button */}
        <div className="flex items-center p-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onToggleSidebar}
            aria-label="Close sidebar"
          >
            <PanelLeftClose className="h-5 w-5" />
          </Button>
        </div>

        {/* Action buttons */}
        <div className="mx-2 space-y-1.5">
          <Button
            variant="outline"
            className="w-full justify-start gap-2 h-9 text-sm rounded-lg"
            onClick={handleNewChat}
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
          <Button
            variant="default"
            className="w-full justify-start gap-2 h-9 text-sm rounded-lg shadow-sm hover:shadow-md transition-shadow"
            onClick={() => {
              onUploadClick();
              // Only close sidebar on mobile where it overlays content
              if (window.innerWidth < 1024) onClose();
            }}
          >
            <Upload className="h-4 w-4" />
            Upload Document
          </Button>
        </div>

        <div className="h-2" />

        {/* Documents section */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="px-3 py-2 flex items-center gap-2">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Documents
            </h3>
            {docCount > 0 && (
              <span className="text-[10px] font-medium bg-primary/10 text-primary px-1.5 py-0.5 rounded-full">
                {docCount}
              </span>
            )}
          </div>
          <ScrollArea className="flex-1">
            <div className="px-2 pr-3">
              <DocumentList isLoading={isLoading} />
            </div>
          </ScrollArea>
        </div>

        {/* Activity Log link */}
        <div className="mx-2 mb-1">
          <Button
            variant={location.pathname === '/app/activity' ? 'secondary' : 'ghost'}
            className="w-full justify-start gap-2 h-9 text-sm rounded-lg"
            onClick={() => {
              navigate('/app/activity');
              if (window.innerWidth < 1024) onClose();
            }}
          >
            <Activity className="h-4 w-4" />
            Activity Log
          </Button>
        </div>

        <div className="mx-3 border-t border-border/30" />

        {/* User section */}
        <div className="p-3">
          <UserMenu />
        </div>
      </aside>
    </>
  );
}
