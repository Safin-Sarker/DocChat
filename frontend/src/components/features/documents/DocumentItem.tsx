import { useState } from 'react';
import { FileText, FileImage, File, Trash2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { UploadedDocument } from '@/types/api';

interface DocumentItemProps {
  document: UploadedDocument;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => Promise<void>;
}

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf':
      return FileText;
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
      return FileImage;
    default:
      return File;
  }
}

function truncateFilename(filename: string, maxLength: number = 24) {
  if (filename.length <= maxLength) return filename;
  const ext = filename.split('.').pop() || '';
  const name = filename.slice(0, filename.lastIndexOf('.'));
  const truncatedName = name.slice(0, maxLength - 3 - ext.length);
  return `${truncatedName}...${ext}`;
}

function formatDate(dateString: string) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function DocumentItem({
  document,
  isActive,
  onSelect,
  onDelete,
}: DocumentItemProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const Icon = getFileIcon(document.filename);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDeleting(true);
    try {
      await onDelete();
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      className={cn(
        'group flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer transition-colors',
        isActive
          ? 'bg-primary/10 text-primary'
          : 'hover:bg-accent text-foreground'
      )}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      <Icon
        className={cn(
          'h-4 w-4 flex-shrink-0',
          isActive ? 'text-primary' : 'text-muted-foreground'
        )}
      />

      <div className="flex-1 min-w-0">
        <Tooltip>
          <TooltipTrigger asChild>
            <p className="text-sm font-medium truncate">
              {truncateFilename(document.filename)}
            </p>
          </TooltipTrigger>
          <TooltipContent side="right" className="max-w-xs">
            <p>{document.filename}</p>
          </TooltipContent>
        </Tooltip>
        <p className="text-xs text-muted-foreground">
          {document.pages} {document.pages === 1 ? 'page' : 'pages'} · {formatDate(document.uploadedAt)}
        </p>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className={cn(
          'h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity',
          isDeleting && 'opacity-100'
        )}
        disabled={isDeleting}
        onClick={handleDelete}
        aria-label="Delete document"
      >
        {isDeleting ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive transition-colors" />
        )}
      </Button>
    </div>
  );
}
