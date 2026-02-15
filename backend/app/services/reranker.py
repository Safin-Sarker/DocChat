"""Reranker wrapper using OpenAI embeddings."""

from typing import List, Dict, Any, Optional
from math import sqrt, ceil
from openai import OpenAI
from app.core.config import settings


class Reranker:
    """Rerank candidate chunks using OpenAI embeddings when available."""

    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as exc:
                print(f"OpenAI client init failed: {exc}")

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sqrt(sum(a * a for a in vec_a))
        norm_b = sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank documents by relevance with balanced document coverage.

        When results come from multiple documents, ensures each document
        gets at least a minimum number of slots in the final results.
        """
        if not docs:
            return []

        if not self.openai_client:
            return self._balanced_select(docs, top_k)

        try:
            return await self._rerank_with_openai(query, docs, top_k)
        except Exception as exc:
            print(f"OpenAI reranking failed: {exc}")
            return self._balanced_select(docs, top_k)

    # Minimum cosine similarity for a chunk to be considered relevant.
    # Chunks below this threshold are dropped before balanced selection.
    RELEVANCE_THRESHOLD = 0.75

    async def _rerank_with_openai(
        self, query: str, docs: List[Dict[str, Any]], top_k: int
    ) -> List[Dict[str, Any]]:
        texts = [doc.get("text", "") for doc in docs]
        response = self.openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=[query] + texts,
        )
        query_vec = response.data[0].embedding
        doc_vecs = [item.embedding for item in response.data[1:]]
        scores = [
            self._cosine_similarity(query_vec, doc_vec)
            for doc_vec in doc_vecs
        ]

        # Score and sort all docs
        scored_docs = [(scores[i], docs[i]) for i in range(len(docs))]
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Drop chunks below the relevance threshold so irrelevant documents
        # don't get forced into results by balanced selection.
        scored_docs = [
            (s, d) for s, d in scored_docs if s >= self.RELEVANCE_THRESHOLD
        ]

        if not scored_docs:
            # Fallback: nothing passed the threshold, return the best we have
            scored_docs = [(scores[i], docs[i]) for i in range(len(docs))]
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            return [doc for _, doc in scored_docs[:top_k]]

        # Find best score per document to detect irrelevant documents
        best_per_doc: Dict[str, float] = {}
        for score, doc in scored_docs:
            did = doc.get("metadata", {}).get("doc_id")
            if did:
                if did not in best_per_doc or score > best_per_doc[did]:
                    best_per_doc[did] = score

        # If only one document or no doc_ids, return top K globally
        if len(best_per_doc) <= 1:
            return [doc for _, doc in scored_docs[:top_k]]

        # Drop documents whose best chunk scores much lower than the
        # top document — they are likely irrelevant to the query.
        top_doc_score = max(best_per_doc.values())
        DOC_GAP_THRESHOLD = 0.05
        relevant_doc_ids = {
            did for did, score in best_per_doc.items()
            if top_doc_score - score <= DOC_GAP_THRESHOLD
        }

        # Filter to only chunks from relevant documents
        scored_docs = [
            (s, d) for s, d in scored_docs
            if d.get("metadata", {}).get("doc_id") in relevant_doc_ids
        ]

        if not scored_docs:
            return []

        # If only one relevant document remains, return top K globally
        if len(relevant_doc_ids) <= 1:
            return [doc for _, doc in scored_docs[:top_k]]

        # Balanced selection: guarantee at least min_per_doc from each document
        min_per_doc = max(1, top_k // len(relevant_doc_ids))
        result = []
        doc_counts: Dict[str, int] = {did: 0 for did in relevant_doc_ids}

        # First pass: pick top chunk from each document to guarantee coverage
        for score, doc in scored_docs:
            did = doc.get("metadata", {}).get("doc_id", "")
            if did in doc_counts and doc_counts[did] < min_per_doc:
                result.append(doc)
                doc_counts[did] += 1

        # Second pass: fill remaining slots with highest-scored chunks
        remaining = top_k - len(result)
        result_ids = {id(d) for d in result}
        for score, doc in scored_docs:
            if remaining <= 0:
                break
            if id(doc) not in result_ids:
                result.append(doc)
                remaining -= 1

        return result[:top_k]

    @staticmethod
    def _balanced_select(docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Fallback selection with balanced document coverage."""
        doc_id_set = set()
        for doc in docs:
            did = doc.get("metadata", {}).get("doc_id")
            if did:
                doc_id_set.add(did)

        if len(doc_id_set) <= 1:
            return docs[:top_k]

        min_per_doc = max(1, top_k // len(doc_id_set))
        result = []
        doc_counts: Dict[str, int] = {did: 0 for did in doc_id_set}

        for doc in docs:
            did = doc.get("metadata", {}).get("doc_id", "")
            if did in doc_counts and doc_counts[did] < min_per_doc:
                result.append(doc)
                doc_counts[did] += 1

        result_ids = {id(d) for d in result}
        for doc in docs:
            if len(result) >= top_k:
                break
            if id(doc) not in result_ids:
                result.append(doc)

        return result[:top_k]
