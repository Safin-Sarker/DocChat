import type { ReflectionScore, SSECacheEvent, SourceMapEntry } from '../query/types';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Array<Record<string, any>>;
  contexts?: string[];
  source_map?: SourceMapEntry[];
  reflection?: ReflectionScore | null;
  cache?: SSECacheEvent;
}
