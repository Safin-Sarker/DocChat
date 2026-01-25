// Query Types
export interface QueryRequest {
  query: string;
}

export interface QueryResponse {
  answer: string;
  contexts: string[];
  sources: Array<Record<string, any>>;
  entities: string[];
}

// Document Upload Types
export interface DocumentUploadResponse {
  doc_id: string;
  storage_path: string;
  pages: number;
  parent_chunks: number;
  child_chunks: number;
  table_chunks: number;
  images: number;
  upserted_vectors: number;
}

// Graph Types
export interface GraphQueryRequest {
  entities: string[];
  max_depth?: number;
  limit?: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphQueryResponse {
  nodes: GraphNode[];
}

// Health Check Types
export interface HealthCheckResponse {
  status: string;
  message?: string;
}

// Message Types (for chat interface)
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<Record<string, any>>;
  contexts?: string[];
}

// API Error Types
export interface ApiError {
  detail: string;
  status?: number;
}
