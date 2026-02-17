import { useEffect, useMemo, useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { api } from '@/api/client';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import type { UploadedDocument } from '@/types/api';

interface DocumentPreviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  document: UploadedDocument | null;
}

function getExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || '';
}

function canInlinePreview(ext: string): boolean {
  return ext === 'pdf' || ['png', 'jpg', 'jpeg', 'gif'].includes(ext);
}

export function DocumentPreviewDialog({
  open,
  onOpenChange,
  document,
}: DocumentPreviewDialogProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ext = useMemo(() => getExtension(document?.filename || ''), [document?.filename]);
  const isInline = canInlinePreview(ext);

  useEffect(() => {
    let active = true;
    const fetchPreview = async () => {
      if (!open || !document) return;

      setIsLoading(true);
      setError(null);
      try {
        const blob = await api.getDocumentFile(document.doc_id);
        if (!active) return;
        const url = URL.createObjectURL(blob);
        setBlobUrl(url);
      } catch (err: any) {
        if (!active) return;
        setError(err?.detail || err?.message || 'Failed to load document');
      } finally {
        if (active) setIsLoading(false);
      }
    };

    fetchPreview();

    return () => {
      active = false;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      setBlobUrl(null);
      setError(null);
    };
  }, [open, document?.doc_id]);

  const handleDownload = () => {
    if (!blobUrl || !document) return;
    const a = window.document.createElement('a');
    a.href = blobUrl;
    a.download = document.filename;
    a.click();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl w-[95vw] h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="truncate">{document?.filename || 'Document Preview'}</DialogTitle>
          <DialogDescription>
            Preview uploaded document content
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 border rounded-md overflow-hidden bg-muted/20">
          {isLoading && (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              Loading preview...
            </div>
          )}

          {!isLoading && error && (
            <div className="h-full flex items-center justify-center text-sm text-destructive px-4 text-center">
              {error}
            </div>
          )}

          {!isLoading && !error && blobUrl && isInline && ext === 'pdf' && (
            <iframe
              src={blobUrl}
              title={document?.filename}
              className="w-full h-full border-0"
            />
          )}

          {!isLoading && !error && blobUrl && isInline && ext !== 'pdf' && (
            <div className="h-full w-full flex items-center justify-center p-4 bg-background">
              <img
                src={blobUrl}
                alt={document?.filename}
                className="max-h-full max-w-full object-contain"
              />
            </div>
          )}

          {!isLoading && !error && blobUrl && !isInline && (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground px-4 text-center">
              Inline preview is not available for this format. Use download to open it.
            </div>
          )}
        </div>

        <div className="flex justify-end">
          <Button variant="outline" onClick={handleDownload} disabled={!blobUrl}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
