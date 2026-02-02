import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, FileText, Trash2, FolderOpen, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useChatStore } from '@/stores/chatStore';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/api/client';
import { cn } from '@/lib/utils';

export function DocumentSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated } = useAuthStore();
  const {
    uploadedDocuments,
    currentDocId,
    setCurrentDoc,
    removeUploadedDocument,
    setUploadedDocuments
  } = useChatStore();

  // Fetch documents from backend on mount and when authenticated
  useEffect(() => {
    const fetchDocuments = async () => {
      if (!isAuthenticated) return;

      setIsLoading(true);
      try {
        const docs = await api.getDocuments();
        setUploadedDocuments(docs);
      } catch (error) {
        console.error('Failed to fetch documents:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, [isAuthenticated, setUploadedDocuments]);

  const handleDelete = async (docId: string) => {
    setDeletingDocId(docId);
    try {
      await api.deleteDocument(docId);
      removeUploadedDocument(docId);
    } catch (error) {
      console.error('Failed to delete document:', error);
      // Still remove from UI even on error
      removeUploadedDocument(docId);
    } finally {
      setDeletingDocId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const truncateFilename = (filename: string, maxLength: number = 20) => {
    if (filename.length <= maxLength) return filename;
    const ext = filename.split('.').pop();
    const name = filename.slice(0, filename.lastIndexOf('.'));
    const truncatedName = name.slice(0, maxLength - 3 - (ext?.length || 0));
    return `${truncatedName}...${ext}`;
  };

  return (
    <div
      className={cn(
        'h-full bg-background border-r transition-all duration-300 flex flex-col',
        isCollapsed ? 'w-12' : 'w-64'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-muted-foreground" />
            <span className="font-medium text-sm">Documents</span>
            <span className="text-xs text-muted-foreground">
              ({uploadedDocuments.length})
            </span>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Document List */}
      {!isCollapsed && (
        <ScrollArea className="flex-1">
          {uploadedDocuments.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No documents uploaded</p>
              <p className="text-xs mt-1">Upload a document to get started</p>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {uploadedDocuments.map((doc) => (
                <div
                  key={doc.doc_id}
                  className={cn(
                    'group flex items-start gap-2 p-2 rounded-md cursor-pointer transition-colors',
                    currentDocId === doc.doc_id
                      ? 'bg-primary/10 border border-primary/20'
                      : 'hover:bg-accent'
                  )}
                  onClick={() => setCurrentDoc(doc.doc_id)}
                >
                  <FileText
                    className={cn(
                      'w-4 h-4 mt-0.5 flex-shrink-0',
                      currentDocId === doc.doc_id
                        ? 'text-primary'
                        : 'text-muted-foreground'
                    )}
                  />
                  <div className="flex-1 min-w-0">
                    <p
                      className={cn(
                        'text-sm font-medium truncate',
                        currentDocId === doc.doc_id && 'text-primary'
                      )}
                      title={doc.filename}
                    >
                      {truncateFilename(doc.filename)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {doc.pages} {doc.pages === 1 ? 'page' : 'pages'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(doc.uploadedAt)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    disabled={deletingDocId === doc.doc_id}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(doc.doc_id);
                    }}
                  >
                    {deletingDocId === doc.doc_id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3 text-destructive" />
                    )}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      )}

      {/* Collapsed state - show icons only */}
      {isCollapsed && (
        <ScrollArea className="flex-1">
          <div className="p-1 space-y-1">
            {uploadedDocuments.map((doc) => (
              <Button
                key={doc.doc_id}
                variant={currentDocId === doc.doc_id ? 'secondary' : 'ghost'}
                size="icon"
                className="w-10 h-10"
                onClick={() => setCurrentDoc(doc.doc_id)}
                title={doc.filename}
              >
                <FileText
                  className={cn(
                    'h-4 w-4',
                    currentDocId === doc.doc_id
                      ? 'text-primary'
                      : 'text-muted-foreground'
                  )}
                />
              </Button>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
