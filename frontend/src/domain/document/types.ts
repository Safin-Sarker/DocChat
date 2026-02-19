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

export interface UploadedDocument {
  doc_id: string;
  filename: string;
  pages: number;
  uploadedAt: string;
}

export interface DeleteDocumentResponse {
  status: 'deleted' | 'partial';
  doc_id: string;
  errors?: string[];
}
