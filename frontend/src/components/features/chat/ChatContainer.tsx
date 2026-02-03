import { useRAGQuery } from '@/hooks/useQuery';
import { useChatStore } from '@/stores/chatStore';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { WelcomeScreen } from './WelcomeScreen';

export function ChatContainer() {
  const {
    messages,
    addMessage,
    setLoading,
    currentDocId,
    setEntities,
    isLoading,
  } = useChatStore();
  const { mutate: queryRAG, isPending } = useRAGQuery();

  const handleSubmit = (userMessage: string) => {
    if (!currentDocId) return;

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

          if (response.entities && response.entities.length > 0) {
            setEntities(response.entities);
          }
          setLoading(false);
        },
        onError: () => {
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

  const handleRegenerate = (messageId: string) => {
    // Find the user message before this assistant message
    const messageIndex = messages.findIndex((m) => m.id === messageId);
    if (messageIndex <= 0) return;

    const userMessage = messages[messageIndex - 1];
    if (userMessage.role !== 'user') return;

    // Remove the current assistant message and regenerate
    useChatStore.setState((state) => ({
      messages: state.messages.slice(0, messageIndex),
    }));

    // Resubmit the user message
    handleSubmit(userMessage.content);
  };

  // Show welcome screen if no messages
  if (messages.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <WelcomeScreen hasDocument={!!currentDocId} />
        {currentDocId && (
          <ChatInput
            onSubmit={handleSubmit}
            disabled={!currentDocId}
            isLoading={isPending || isLoading}
          />
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <ChatMessages
        messages={messages}
        isLoading={isPending || isLoading}
        onRegenerate={handleRegenerate}
      />
      <ChatInput
        onSubmit={handleSubmit}
        disabled={!currentDocId}
        isLoading={isPending || isLoading}
      />
    </div>
  );
}
