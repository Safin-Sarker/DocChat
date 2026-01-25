import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MessageSquare } from 'lucide-react';
import { Message } from './Message';
import { useRAGQuery } from '@/hooks/useQuery';
import { useChatStore } from '@/stores/chatStore';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

export const ChatInterface = () => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, addMessage, setLoading, currentDocId, setEntities } = useChatStore();
  const { mutate: queryRAG, isPending } = useRAGQuery();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isPending) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message
    addMessage({
      role: 'user',
      content: userMessage,
    });

    // Add placeholder assistant message
    addMessage({
      role: 'assistant',
      content: '',
    });

    setLoading(true);

    // Query RAG
    queryRAG(
      { query: userMessage },
      {
        onSuccess: (response) => {
          // Update the last message with the response
          useChatStore.setState((state) => {
            const newMessages = [...state.messages];
            if (newMessages.length > 0) {
              newMessages[newMessages.length - 1] = {
                ...newMessages[newMessages.length - 1],
                content: response.answer,
                sources: response.sources,
                contexts: response.contexts,
              };
            }
            return { messages: newMessages };
          });
          // Store entities for graph visualization
          console.log('ChatInterface: response entities', response.entities);
          if (response.entities && response.entities.length > 0) {
            console.log('ChatInterface: setting entities', response.entities);
            setEntities(response.entities);
          }
          setLoading(false);
        },
        onError: () => {
          // Update with error message
          useChatStore.setState((state) => {
            const newMessages = [...state.messages];
            if (newMessages.length > 0) {
              newMessages[newMessages.length - 1] = {
                ...newMessages[newMessages.length - 1],
                content: 'Sorry, I encountered an error processing your query. Please try again.',
              };
            }
            return { messages: newMessages };
          });
          setLoading(false);
        },
      }
    );
  };

  return (
    <Card className="flex flex-col h-full shadow-xl border-2">
      <div className="flex items-center gap-3 p-4 border-b bg-accent/30">
        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10">
          <MessageSquare className="w-5 h-5 text-primary" />
        </div>
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-foreground">Chat</h2>
          <p className="text-sm text-muted-foreground">
            {currentDocId ? `Document loaded` : 'Upload a document to start'}
          </p>
        </div>
      </div>

      <ScrollArea className="flex-1 p-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
            <MessageSquare className="w-16 h-16 text-muted-foreground" />
            <div>
              <p className="text-lg font-medium text-foreground">No messages yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Upload a document and start asking questions
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}
            {isPending && (
              <div className="flex gap-4 mb-6 justify-start animate-in fade-in-50">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                </div>
                <Card className="bg-card p-4 shadow-md">
                  <div className="flex gap-2 items-center text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </Card>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </ScrollArea>

      <div className="p-4 border-t bg-accent/20">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              currentDocId
                ? 'Ask a question about your document...'
                : 'Upload a document first...'
            }
            disabled={!currentDocId || isPending}
            className="flex-1 bg-background"
          />
          <Button
            type="submit"
            disabled={!currentDocId || !input.trim() || isPending}
            size="icon"
            className="shrink-0"
          >
            {isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </form>
      </div>
    </Card>
  );
};
