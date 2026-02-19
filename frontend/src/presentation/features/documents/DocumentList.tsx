import { useState, useMemo } from 'react';
import { FileText, Check, Search, X } from 'lucide-react';
import { toast } from 'sonner';
import { useAppSelector, useAppDispatch } from '@/infrastructure/store/hooks';
import { toggleDocSelection, setSelectAllDocs, removeUploadedDocument } from '@/infrastructure/store/slices/chatSlice';
import { deleteDocument } from '@/infrastructure/api/document.api';
import { DocumentItem } from './DocumentItem';
import { DeleteConfirmDialog } from './DeleteConfirmDialog';
import { DocumentPreviewDialog } from './DocumentPreviewDialog';
import { EmptyState } from '@/presentation/shared/EmptyState';
import { Skeleton } from '@/presentation/ui/skeleton';
import { cn } from '@/lib/utils';
import type { UploadedDocument } from '@/domain/document/types';

interface DocumentListProps {
  isLoading: boolean;
}

export function DocumentList({ isLoading }: DocumentListProps) {
  const [deleteDoc, setDeleteDoc] = useState<UploadedDocument | null>(null);
  const [previewDoc, setPreviewDoc] = useState<UploadedDocument | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const dispatch = useAppDispatch();
  const uploadedDocuments = useAppSelector((s) => s.chat.uploadedDocuments);
  const selectedDocIds = useAppSelector((s) => s.chat.selectedDocIds);
  const selectAllDocsFlag = useAppSelector((s) => s.chat.selectAllDocs);

  const filteredDocuments = useMemo(() => {
    if (!searchQuery.trim()) return uploadedDocuments;
    const query = searchQuery.toLowerCase();
    return uploadedDocuments.filter((doc) =>
      doc.filename.toLowerCase().includes(query)
    );
  }, [uploadedDocuments, searchQuery]);

  const handleDelete = async (doc: UploadedDocument) => {
    try {
      await deleteDocument(doc.doc_id);
      dispatch(removeUploadedDocument(doc.doc_id));
      toast.success('Document deleted', {
        description: doc.filename,
      });
    } catch (error) {
      console.error('Failed to delete document:', error);
      dispatch(removeUploadedDocument(doc.doc_id));
      toast.error('Failed to delete', {
        description: 'Document removed from list',
      });
    }
    setDeleteDoc(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-2 p-1">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-2 px-2 py-2">
            <Skeleton className="h-4 w-4 rounded" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (uploadedDocuments.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No documents"
        description="Upload a document to start chatting"
        className="py-8"
      />
    );
  }

  return (
    <>
      <div className="space-y-1 p-1">
        {/* Search input — only show when 3+ documents */}
        {uploadedDocuments.length >= 3 && (
          <div className="relative px-1 pb-2">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-8 pl-8 pr-8 text-sm bg-muted/50 border border-border/50 rounded-md placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        )}

        {/* "All Documents" option */}
        {uploadedDocuments.length > 1 && !searchQuery && (
          <div
            className={cn(
              'flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer transition-colors',
              selectAllDocsFlag ? 'bg-primary/10 text-primary' : 'hover:bg-accent'
            )}
            onClick={() => dispatch(setSelectAllDocs(!selectAllDocsFlag))}
            role="checkbox"
            aria-checked={selectAllDocsFlag}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                dispatch(setSelectAllDocs(!selectAllDocsFlag));
              }
            }}
          >
            <div
              className={cn(
                'flex-shrink-0 w-4 h-4 rounded border transition-colors flex items-center justify-center',
                selectAllDocsFlag
                  ? 'bg-primary border-primary'
                  : 'border-muted-foreground/40'
              )}
            >
              {selectAllDocsFlag && <Check className="w-3 h-3 text-primary-foreground" />}
            </div>
            <span className="text-sm font-medium">All Documents</span>
          </div>
        )}

        {filteredDocuments.length === 0 && searchQuery ? (
          <div className="px-2 py-6 text-center">
            <p className="text-sm text-muted-foreground">No matches found</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Try a different search term</p>
          </div>
        ) : (
          filteredDocuments.map((doc) => (
            <DocumentItem
              key={doc.doc_id}
              document={doc}
              isSelected={selectedDocIds.includes(doc.doc_id)}
              onToggle={() => dispatch(toggleDocSelection(doc.doc_id))}
              onPreview={() => setPreviewDoc(doc)}
              onDelete={async () => setDeleteDoc(doc)}
            />
          ))
        )}
      </div>

      <DeleteConfirmDialog
        open={!!deleteDoc}
        onOpenChange={(open) => !open && setDeleteDoc(null)}
        documentName={deleteDoc?.filename || ''}
        onConfirm={() => deleteDoc && handleDelete(deleteDoc)}
      />

      <DocumentPreviewDialog
        open={!!previewDoc}
        onOpenChange={(open) => !open && setPreviewDoc(null)}
        document={previewDoc}
      />
    </>
  );
}
