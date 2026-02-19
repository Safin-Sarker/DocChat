"""Pinecone vector store wrapper for multimodal embeddings."""

from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.services.cache_utils import TTLCache


class PineconeStore:
    """Wrapper for Pinecone vector database operations."""
    _embedding_cache: Optional[TTLCache[str, List[float]]] = None

    def __init__(self):
        """Initialize Pinecone connection."""
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = None
        if settings.ENABLE_EMBEDDING_CACHE and PineconeStore._embedding_cache is None:
            PineconeStore._embedding_cache = TTLCache(
                max_size=settings.EMBEDDING_CACHE_MAX_SIZE,
                ttl_seconds=settings.EMBEDDING_CACHE_TTL_SECONDS,
            )
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
            cache = PineconeStore._embedding_cache if settings.ENABLE_EMBEDDING_CACHE else None
            if cache:
                cached = cache.get(text)
                if cached is not None:
                    return cached
            embedding = self.embeddings.embed_query(text)
            if cache:
                cache.set(text, embedding)
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get OpenAI embeddings for multiple texts in a single batch call.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []

            cache = PineconeStore._embedding_cache if settings.ENABLE_EMBEDDING_CACHE else None
            if not cache:
                return self.embeddings.embed_documents(texts)

            # Preserve order and duplicates while minimizing embed calls
            unique_missing: Dict[str, None] = {}
            for text in texts:
                if cache.get(text) is None:
                    unique_missing[text] = None

            if unique_missing:
                missing_texts = list(unique_missing.keys())
                missing_embeddings = self.embeddings.embed_documents(missing_texts)
                for text, embedding in zip(missing_texts, missing_embeddings):
                    cache.set(text, embedding)

            results: List[List[float]] = []
            for text in texts:
                embedding = cache.get(text)
                if embedding is None:
                    embedding = self.embeddings.embed_query(text)
                    cache.set(text, embedding)
                results.append(embedding)

            return results
        except Exception as e:
            print(f"Error getting batch embeddings: {e}")
            raise

    async def upsert_vectors(self, vectors: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """Upsert vectors to Pinecone in batches.

        Args:
            vectors: List of vector dictionaries with id, values, metadata
            batch_size: Number of vectors per batch (default 100)

        Returns:
            Dictionary with upsert statistics
        """
        try:
            if not vectors:
                return {"upserted": 0}

            # Upsert in batches to avoid API limits
            total_upserted = 0
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                total_upserted += len(batch)

            return {
                "upserted": total_upserted,
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
        user_id: Optional[str] = None,
        doc_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Query Pinecone using text (automatically generates embedding).

        Args:
            query_text: Query text
            top_k: Number of results to return
            filter: Metadata filter
            user_id: User ID for filtering (required for multi-tenant isolation)
            doc_ids: List of document IDs to filter by (empty/None = all documents)

        Returns:
            List of matching results
        """
        # Build filter with user_id for multi-tenant isolation
        query_filter = filter.copy() if filter else {}
        if user_id:
            query_filter["user_id"] = user_id
        if doc_ids:
            query_filter["doc_id"] = {"$in": doc_ids}

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
