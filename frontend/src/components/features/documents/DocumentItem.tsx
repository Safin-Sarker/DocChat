import { useState } from 'react';
import { FileText, FileImage, FileSpreadsheet, File, Trash2, Loader2, Check, Eye } from 'lucide-react';
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
  isSelected: boolean;
  onToggle: () => void;
  onPreview: () => void;
  onDelete: () => Promise<void>;
}

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf':
    case 'docx':
      return FileText;
    case 'xlsx':
    case 'xls':
      return FileSpreadsheet;
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
      return FileImage;
    default:
      return File;
  }
}

function truncateFilename(filename: string, maxLength: number = 20) {
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
  isSelected,
  onToggle,
  onPreview,
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
        'group flex items-center gap-1.5 px-1.5 py-2 rounded-lg cursor-pointer transition-colors duration-200',
        isSelected
          ? 'bg-primary/10 text-primary ring-1 ring-primary/20'
          : 'hover:bg-accent text-foreground'
      )}
      onClick={onToggle}
      role="checkbox"
      aria-checked={isSelected}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onToggle();
        }
      }}
    >
      {/* Checkbox indicator */}
      <div
        className={cn(
          'flex-shrink-0 w-4 h-4 rounded border transition-colors flex items-center justify-center',
          isSelected
            ? 'bg-primary border-primary'
            : 'border-muted-foreground/40'
        )}
      >
        {isSelected && <Check className="w-3 h-3 text-primary-foreground" />}
      </div>

      <Icon
        className={cn(
          'h-4 w-4 flex-shrink-0',
          isSelected ? 'text-primary' : 'text-muted-foreground'
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
        <p className="text-[11px] text-muted-foreground/70">
          {document.pages} {document.pages === 1 ? 'page' : 'pages'} · {formatDate(document.uploadedAt)}
        </p>
      </div>

      <div className="flex items-center gap-0.5 flex-shrink-0 ml-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 min-w-[24px] text-muted-foreground/80 hover:text-foreground transition-colors duration-200"
          onClick={(e) => {
            e.stopPropagation();
            onPreview();
          }}
          aria-label="Preview document"
        >
          <Eye className="h-3.5 w-3.5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className={cn(
            'h-6 w-6 min-w-[24px] text-muted-foreground/80 hover:text-destructive transition-colors duration-200',
            isDeleting ? 'text-destructive' : ''
          )}
          disabled={isDeleting}
          onClick={handleDelete}
          aria-label="Delete document"
        >
          {isDeleting ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Trash2 className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>
    </div>
  );
}
