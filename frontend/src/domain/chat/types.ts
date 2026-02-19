import type { ReflectionScore, SSECacheEvent } from '../query/types';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<Record<string, any>>;
  contexts?: string[];
  reflection?: ReflectionScore | null;
  cache?: SSECacheEvent;
}
