"""Pinecone vector store wrapper for multimodal embeddings."""

from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


class PineconeStore:
    """Wrapper for Pinecone vector database operations."""

    def __init__(self):
        """Initialize Pinecone connection."""
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = None
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Create Pinecone index if it doesn't exist."""
        try:
            # Check if index exists
            existing_indexes = self.client.list_indexes()
            index_names = [idx.name for idx in existing_indexes]

            if self.index_name not in index_names:
                print(f"Creating Pinecone index: {self.index_name}")
                self.client.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI ada-002 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
                print(f"Index {self.index_name} created successfully")

            # Connect to index
            self.index = self.client.Index(self.index_name)
            print(f"Connected to Pinecone index: {self.index_name}")

        except Exception as e:
            print(f"Error ensuring Pinecone index exists: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise

    async def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert vectors to Pinecone.

        Args:
            vectors: List of vector dictionaries with id, values, metadata

        Returns:
            Dictionary with upsert statistics
        """
        try:
            if not vectors:
                return {"upserted": 0}

            # Upsert to Pinecone
            self.index.upsert(vectors=vectors)

            return {
                "upserted": len(vectors),
                "index": self.index_name
            }
        except Exception as e:
            print(f"Error upserting vectors: {e}")
            raise

    async def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Query Pinecone for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filter
            include_metadata: Whether to include metadata in results

        Returns:
            List of matching results with scores and metadata
        """
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter,
                include_metadata=include_metadata
            )

            matches = []
            for match in results.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {}
                })

            return matches
        except Exception as e:
            print(f"Error querying Pinecone: {e}")
            raise

    async def query_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query Pinecone using text (automatically generates embedding).

        Args:
            query_text: Query text
            top_k: Number of results to return
            filter: Metadata filter
            user_id: User ID for filtering (required for multi-tenant isolation)

        Returns:
            List of matching results
        """
        # Build filter with user_id for multi-tenant isolation
        query_filter = filter.copy() if filter else {}
        if user_id:
            query_filter["user_id"] = user_id

        query_vector = await self.get_embedding(query_text)
        return await self.query(query_vector, top_k, query_filter if query_filter else None)

    async def delete_by_doc_id(self, doc_id: str, user_id: Optional[str] = None):
        """Delete all vectors for a document.

        Args:
            doc_id: Document ID to delete
            user_id: User ID for multi-tenant isolation
        """
        try:
            filter_dict = {"doc_id": doc_id}
            if user_id:
                filter_dict["user_id"] = user_id

            self.index.delete(filter=filter_dict)
            print(f"Deleted vectors for document: {doc_id}" + (f" (user: {user_id})" if user_id else ""))
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics.

        Returns:
            Index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_name": self.index_name
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
