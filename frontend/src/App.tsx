import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, Network, FileUp } from 'lucide-react';
import { DocumentUpload } from '@/components/DocumentUpload';
import { ChatInterface } from '@/components/ChatInterface';
import { GraphVisualization } from '@/components/GraphVisualization';
import { useChatStore } from '@/stores/chatStore';
import { api } from '@/api/client';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const { entities, serverSessionId, setServerSessionId, clearMessages } = useChatStore();

  useEffect(() => {
    const checkSession = async () => {
      try {
        const health = await api.healthCheck();
        if (health.session_id && health.session_id !== serverSessionId) {
          clearMessages();
          setServerSessionId(health.session_id);
        }
      } catch (error) {
        console.error('Failed to check server session:', error);
      }
    };
    checkSession();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/20">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-lg">
                <MessageSquare className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                  DocChat Advanced RAG
                </h1>
                <p className="text-sm text-muted-foreground">
                  Multimodal Document Intelligence Platform
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent/50 border">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs font-medium text-muted-foreground">Connected</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Upload */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              <DocumentUpload />
            </div>
          </div>

          {/* Right Column - Chat & Graph */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="chat" className="h-[calc(100vh-12rem)]">
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  <span>Chat</span>
                </TabsTrigger>
                <TabsTrigger value="graph" className="flex items-center gap-2">
                  <Network className="w-4 h-4" />
                  <span>Knowledge Graph</span>
                </TabsTrigger>
              </TabsList>
              <TabsContent value="chat" className="h-full m-0">
                <ChatInterface />
              </TabsContent>
              <TabsContent value="graph" className="h-full m-0">
                <GraphVisualization entities={entities} />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-12 bg-background/95 backdrop-blur">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <FileUp className="w-4 h-4" />
              <span>Upload documents to get started</span>
            </div>
            <div>
              Powered by OpenAI GPT-4 & Pinecone Vector Database
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
