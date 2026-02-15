import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSubmit,
  disabled = false,
  isLoading = false,
  placeholder = 'Ask about your document...',
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled || isLoading) return;
    onSubmit(trimmed);
    setInput('');
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="bg-gradient-to-t from-background via-background to-background/80 backdrop-blur-safe">
      <div className="max-w-3xl mx-auto p-4">
        <div
          className={cn(
            'relative flex items-end gap-2 rounded-2xl border border-border/60 bg-background shadow-[0_2px_12px_-2px_rgb(0_0_0/0.08)] transition-all',
            !disabled && 'focus-within:shadow-[0_2px_16px_-2px_rgb(0_0_0/0.12)] focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/10',
            disabled && 'opacity-60'
          )}
        >
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? 'Select a document to start chatting...' : placeholder}
            disabled={disabled || isLoading}
            className="min-h-[44px] max-h-[200px] resize-none border-0 bg-transparent px-4 py-3 focus-visible:ring-0 focus-visible:ring-offset-0 scrollbar-thin"
            rows={1}
          />
          <Button
            onClick={handleSubmit}
            disabled={disabled || !input.trim() || isLoading}
            size="icon"
            className="absolute right-2 bottom-2 h-8 w-8 rounded-xl transition-transform hover:scale-105 active:scale-95"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="mt-2 text-[11px] text-center text-muted-foreground/50">
          Press Enter to send, Shift + Enter for new line
        </p>
      </div>
    </div>
  );
}
