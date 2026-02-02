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

// Uploaded Document (for tracking in sidebar)
export interface UploadedDocument {
  doc_id: string;
  filename: string;
  pages: number;
  uploadedAt: string;
}

// Delete Document Response
export interface DeleteDocumentResponse {
  status: 'deleted' | 'partial';
  doc_id: string;
  errors?: string[];
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
  session_id?: string;
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

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface UserInfo {
  user_id: string;
  email: string;
  username: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}
