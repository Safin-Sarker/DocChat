export interface QueryRequest {
  query: string;
  chat_history?: Array<{ role: string; content: string }>;
  doc_ids?: string[];
}

export type SSEStage = 'routing' | 'retrieving' | 'reranking' | 'generating' | 'evaluating' | 'improving' | 'extracting';

export interface SSETokenEvent {
  content: string;
  replace?: boolean;
}

export interface SSESourcesEvent {
  sources: Array<Record<string, any>>;
  contexts: string[];
}

export type CacheType = 'exact' | 'semantic' | 'none';

export interface SSECacheEvent {
  cache_hit: boolean;
  cache_type: CacheType;
}

export interface ReflectionScore {
  faithfulness: number;
  relevance: number;
  completeness: number;
  coherence: number;
  conciseness: number;
  overall: number;
  verdict: string;
  feedback: string;
  was_regenerated: boolean;
}

export interface QueryResponse {
  answer: string;
  contexts: string[];
  sources: Array<Record<string, any>>;
  entities: string[];
  reflection?: ReflectionScore | null;
}
