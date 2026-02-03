import { useState } from 'react';
import { FileText } from 'lucide-react';
import { toast } from 'sonner';
import { useChatStore } from '@/stores/chatStore';
import { api } from '@/api/client';
import { DocumentItem } from './DocumentItem';
import { DeleteConfirmDialog } from './DeleteConfirmDialog';
import { EmptyState } from '@/components/shared/EmptyState';
import { Skeleton } from '@/components/ui/skeleton';
import type { UploadedDocument } from '@/types/api';

interface DocumentListProps {
  isLoading: boolean;
}

export function DocumentList({ isLoading }: DocumentListProps) {
  const [deleteDoc, setDeleteDoc] = useState<UploadedDocument | null>(null);
  const {
    uploadedDocuments,
    currentDocId,
    setCurrentDoc,
    removeUploadedDocument,
  } = useChatStore();

  const handleDelete = async (doc: UploadedDocument) => {
    try {
      await api.deleteDocument(doc.doc_id);
      removeUploadedDocument(doc.doc_id);
      toast.success('Document deleted', {
        description: doc.filename,
      });
    } catch (error) {
      console.error('Failed to delete document:', error);
      removeUploadedDocument(doc.doc_id);
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
        {uploadedDocuments.map((doc) => (
          <DocumentItem
            key={doc.doc_id}
            document={doc}
            isActive={currentDocId === doc.doc_id}
            onSelect={() => setCurrentDoc(doc.doc_id)}
            onDelete={async () => setDeleteDoc(doc)}
          />
        ))}
      </div>

      <DeleteConfirmDialog
        open={!!deleteDoc}
        onOpenChange={(open) => !open && setDeleteDoc(null)}
        documentName={deleteDoc?.filename || ''}
        onConfirm={() => deleteDoc && handleDelete(deleteDoc)}
      />
    </>
  );
}
