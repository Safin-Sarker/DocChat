import { Upload, MessageSquare, FileText, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Logo } from '@/components/shared/Logo';
import { useUploadModal } from '@/hooks/useUploadModal';

interface WelcomeScreenProps {
  hasDocument: boolean;
  hasUploadedDocs?: boolean;
}

export function WelcomeScreen({ hasDocument, hasUploadedDocs = false }: WelcomeScreenProps) {
  const { open: openUploadModal } = useUploadModal();

  const heading = hasDocument
    ? 'Start a conversation'
    : hasUploadedDocs
      ? 'Select a document'
      : 'Welcome to DocChat';

  const subtitle = hasDocument
    ? 'Ask questions about your uploaded document'
    : hasUploadedDocs
      ? 'Choose a document from the sidebar to start chatting'
      : 'Upload a document and start asking questions about it';

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-8 animate-in">
      <div className="max-w-lg text-center space-y-8">
        <Logo size="lg" className="justify-center" />

        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight text-foreground text-balance">
            {heading}
          </h1>
          <p className="text-muted-foreground">
            {subtitle}
          </p>
        </div>

        {!hasDocument && !hasUploadedDocs && (
          <Button onClick={openUploadModal} size="lg" className="gap-2">
            <Upload className="h-4 w-4" />
            Upload Document
          </Button>
        )}

        <div className="pt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          <div className="p-4 rounded-xl bg-muted/30 border border-border/50 transition-all duration-200 hover:bg-muted/60 hover:shadow-sm">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <FileText className="h-4 w-4 text-primary" />
            </div>
            <h3 className="font-semibold text-sm mb-1">Multiple Formats</h3>
            <p className="text-xs text-muted-foreground">
              Upload PDFs, DOCX, XLSX files, or images
            </p>
          </div>
          <div className="p-4 rounded-xl bg-muted/30 border border-border/50 transition-all duration-200 hover:bg-muted/60 hover:shadow-sm">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <MessageSquare className="h-4 w-4 text-primary" />
            </div>
            <h3 className="font-semibold text-sm mb-1">Natural Queries</h3>
            <p className="text-xs text-muted-foreground">
              Ask questions in plain language
            </p>
          </div>
          <div className="p-4 rounded-xl bg-muted/30 border border-border/50 transition-all duration-200 hover:bg-muted/60 hover:shadow-sm">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <h3 className="font-semibold text-sm mb-1">Smart Answers</h3>
            <p className="text-xs text-muted-foreground">
              Get accurate responses with sources
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
