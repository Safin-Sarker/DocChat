"""End-to-end RAG pipeline service."""

import asyncio
import copy
import hashlib
import json
import logging
import math
import time
from collections import OrderedDict
from threading import Lock
from typing import Dict, Any, List, Optional, AsyncIterator, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)
from app.services.hybrid_retrieval import HybridRetrieval
from app.services.reranker import Reranker
from app.services.context_assembler import ContextAssembler
from app.services.response_generator import ResponseGenerator
from app.services.entity_extractor import EntityExtractor
from app.services.query_router import QueryRouter
from app.services.answer_judge import AnswerJudge
from app.services.cache_utils import TTLCache
from app.models.document import Document


class AdvancedRAGService:
    """Orchestrate retrieval, reranking, and response generation."""
    _response_cache: Optional[TTLCache[str, Dict[str, Any]]] = None
    _semantic_cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    _semantic_cache_lock = Lock()

    def __init__(
        self,
        retrieval: HybridRetrieval | None = None,
        reranker: Reranker | None = None,
        assembler: ContextAssembler | None = None,
        generator: ResponseGenerator | None = None,
        entity_extractor: EntityExtractor | None = None,
        query_router: QueryRouter | None = None,
    ):
        self.retrieval = retrieval or HybridRetrieval()
        self.reranker = reranker or Reranker()
        self.assembler = assembler or ContextAssembler()
        self.generator = generator or ResponseGenerator()
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.query_router = query_router or QueryRouter()
        self.answer_judge = AnswerJudge() if settings.JUDGE_ENABLED else None
        if settings.ENABLE_QUERY_RESPONSE_CACHE and AdvancedRAGService._response_cache is None:
            AdvancedRAGService._response_cache = TTLCache(
                max_size=settings.QUERY_RESPONSE_CACHE_MAX_SIZE,
                ttl_seconds=settings.QUERY_RESPONSE_CACHE_TTL_SECONDS,
            )

    @staticmethod
    def _normalize_doc_ids(doc_ids: Optional[List[str]]) -> Optional[List[str]]:
        if not doc_ids:
            return None
        normalized = sorted({doc_id for doc_id in doc_ids if doc_id})
        return normalized or None

    @staticmethod
    def _normalize_chat_history(chat_history: Optional[List]) -> List[Dict[str, str]]:
        normalized: List[Dict[str, str]] = []
        for item in chat_history or []:
            role = getattr(item, "role", None)
            content = getattr(item, "content", None)
            if role is None and isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")
            if role and isinstance(content, str):
                normalized.append({"role": str(role), "content": content})
        return normalized

    @staticmethod
    def _build_response_cache_key(
        query: str,
        user_id: Optional[str],
        doc_ids: Optional[List[str]],
        chat_history: Optional[List],
    ) -> str:
        payload = {
            "v": 1,
            "query": (query or "").strip(),
            "user_id": user_id or "",
            "doc_ids": AdvancedRAGService._normalize_doc_ids(doc_ids) or [],
            "chat_history": AdvancedRAGService._normalize_chat_history(chat_history),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if not settings.ENABLE_QUERY_RESPONSE_CACHE or not AdvancedRAGService._response_cache:
            return None
        cached = AdvancedRAGService._response_cache.get(cache_key)
        return copy.deepcopy(cached) if cached else None

    def _set_cached_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        if not settings.ENABLE_QUERY_RESPONSE_CACHE or not AdvancedRAGService._response_cache:
            return
        AdvancedRAGService._response_cache.set(cache_key, copy.deepcopy(response))

    @staticmethod
    def _semantic_cache_scope(
        user_id: Optional[str],
        doc_ids: Optional[List[str]],
        intent: str,
    ) -> str:
        normalized_docs = AdvancedRAGService._normalize_doc_ids(doc_ids) or []
        return f"{user_id or ''}|{intent}|{','.join(normalized_docs)}"

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _semantic_cache_allowed(chat_history: Optional[List]) -> bool:
        if not settings.ENABLE_SEMANTIC_QUERY_CACHE:
            return False
        if not settings.SEMANTIC_CACHE_REQUIRE_EMPTY_HISTORY:
            return True
        normalized_history = AdvancedRAGService._normalize_chat_history(chat_history)
        return len(normalized_history) == 0

    @classmethod
    def _prune_semantic_cache(cls) -> None:
        now = time.time()
        ttl = settings.QUERY_RESPONSE_CACHE_TTL_SECONDS
        with cls._semantic_cache_lock:
            expired_keys = [
                key for key, item in cls._semantic_cache.items()
                if item.get("expires_at", 0) <= now
            ]
            for key in expired_keys:
                cls._semantic_cache.pop(key, None)

            while len(cls._semantic_cache) > settings.QUERY_RESPONSE_CACHE_MAX_SIZE:
                cls._semantic_cache.popitem(last=False)

    async def _get_semantic_cached_response(
        self,
        query: str,
        user_id: Optional[str],
        doc_ids: Optional[List[str]],
        chat_history: Optional[List],
        intent: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[List[float]]]:
        if not self._semantic_cache_allowed(chat_history):
            return None, None

        self._prune_semantic_cache()
        scope = self._semantic_cache_scope(user_id, doc_ids, intent)
        query_embedding = await self.retrieval.pinecone_store.get_embedding(query.strip())

        best_score = -1.0
        best_response: Optional[Dict[str, Any]] = None

        with AdvancedRAGService._semantic_cache_lock:
            for key, item in AdvancedRAGService._semantic_cache.items():
                if item.get("scope") != scope:
                    continue
                score = self._cosine_similarity(query_embedding, item.get("query_embedding", []))
                if score >= settings.SEMANTIC_CACHE_SIMILARITY_THRESHOLD and score > best_score:
                    best_score = score
                    best_response = copy.deepcopy(item.get("response"))
                    AdvancedRAGService._semantic_cache.move_to_end(key)

        if best_response:
            logger.info(f"Semantic response cache hit (intent={intent}, score={best_score:.3f})")
            return best_response, query_embedding
        if best_score >= 0:
            logger.info(
                "Semantic response cache miss "
                f"(intent={intent}, best_score={best_score:.3f}, threshold={settings.SEMANTIC_CACHE_SIMILARITY_THRESHOLD:.3f})"
            )
        else:
            logger.info(
                "Semantic response cache miss "
                f"(intent={intent}, reason=no_candidates_in_scope, threshold={settings.SEMANTIC_CACHE_SIMILARITY_THRESHOLD:.3f})"
            )
        return None, query_embedding

    def _set_semantic_cached_response(
        self,
        query: str,
        response: Dict[str, Any],
        user_id: Optional[str],
        doc_ids: Optional[List[str]],
        chat_history: Optional[List],
        intent: str,
        query_embedding: Optional[List[float]] = None,
    ) -> None:
        if not self._semantic_cache_allowed(chat_history):
            return
        if query_embedding is None:
            return

        cache_key = hashlib.sha256(
            json.dumps(
                {
                    "query": query.strip(),
                    "scope": self._semantic_cache_scope(user_id, doc_ids, intent),
                    "ts_bucket": int(time.time() // 60),
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        with AdvancedRAGService._semantic_cache_lock:
            AdvancedRAGService._semantic_cache[cache_key] = {
                "scope": self._semantic_cache_scope(user_id, doc_ids, intent),
                "query_embedding": query_embedding,
                "response": copy.deepcopy(response),
                "expires_at": time.time() + settings.QUERY_RESPONSE_CACHE_TTL_SECONDS,
            }
            AdvancedRAGService._semantic_cache.move_to_end(cache_key)
        self._prune_semantic_cache()

    @staticmethod
    def _build_doc_names(user_id: Optional[str]) -> Dict[str, str]:
        """Build a doc_id -> filename mapping for context labeling."""
        if not user_id:
            return {}
        try:
            docs = Document.get_by_user(user_id)
            return {d["doc_id"]: d["filename"] for d in docs}
        except Exception as exc:
            logger.warning(f"Failed to build doc_names map: {exc}")
            return {}

    @staticmethod
    def _diversify_by_doc(
        ranked: List[Dict[str, Any]],
        top_k: int,
        doc_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Keep reranked results balanced across selected documents."""
        if not ranked:
            return []

        if not doc_ids or len(doc_ids) <= 1:
            return ranked[:top_k]

        selected: List[Dict[str, Any]] = []
        selected_ids = set()
        per_doc_count: Dict[str, int] = {}
        per_doc_cap = max(2, math.ceil(top_k / len(doc_ids)) + 1)

        # First pass: try to include at least one chunk from each selected doc
        for doc_id in doc_ids:
            for item in ranked:
                item_id = item.get("id")
                item_doc_id = item.get("metadata", {}).get("doc_id")
                if item_id in selected_ids or item_doc_id != doc_id:
                    continue
                selected.append(item)
                selected_ids.add(item_id)
                per_doc_count[doc_id] = per_doc_count.get(doc_id, 0) + 1
                break

        # Second pass: fill remaining slots while capping per-doc dominance
        for item in ranked:
            if len(selected) >= top_k:
                break
            item_id = item.get("id")
            item_doc_id = item.get("metadata", {}).get("doc_id")
            if item_id in selected_ids:
                continue
            if item_doc_id and per_doc_count.get(item_doc_id, 0) >= per_doc_cap:
                continue

            selected.append(item)
            selected_ids.add(item_id)
            if item_doc_id:
                per_doc_count[item_doc_id] = per_doc_count.get(item_doc_id, 0) + 1

        return selected[:top_k]

    @staticmethod
    def _looks_like_multi_doc_summary(query: str) -> bool:
        """Heuristic for broad multi-document summary requests."""
        q = (query or "").lower()
        return any(token in q for token in ["these documents", "all documents", "documents", "all docs", "docs"])

    @staticmethod
    def _ensure_doc_coverage(
        ranked: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        doc_ids: Optional[List[str]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Ensure at least one chunk per selected document when possible."""
        if not doc_ids or len(doc_ids) <= 1:
            return ranked[:top_k]

        selected = list(ranked[:top_k])
        selected_ids = {item.get("id") for item in selected}
        covered_doc_ids = {
            item.get("metadata", {}).get("doc_id")
            for item in selected
            if item.get("metadata", {}).get("doc_id")
        }

        for doc_id in doc_ids:
            if doc_id in covered_doc_ids:
                continue
            replacement = next(
                (
                    item for item in candidates
                    if item.get("metadata", {}).get("doc_id") == doc_id
                    and item.get("id") not in selected_ids
                ),
                None
            )
            if not replacement:
                continue

            if len(selected) >= top_k and selected:
                selected.pop()
            if len(selected) < top_k:
                selected.append(replacement)
                selected_ids.add(replacement.get("id"))
                covered_doc_ids.add(doc_id)

        return selected[:top_k]

    @staticmethod
    def _resolve_summary_doc_ids(
        query: str,
        user_id: Optional[str],
        doc_ids: Optional[List[str]],
    ) -> Optional[List[str]]:
        """Resolve effective doc_ids for summary-style multi-document queries."""
        if doc_ids:
            return doc_ids
        if not user_id or not AdvancedRAGService._looks_like_multi_doc_summary(query):
            return doc_ids

        try:
            docs = Document.get_by_user(user_id)
            all_doc_ids = [d.get("doc_id") for d in docs if d.get("doc_id")]
            return all_doc_ids or None
        except Exception as exc:
            logger.warning(f"Failed to resolve all doc_ids for summary: {exc}")
            return doc_ids

    @staticmethod
    def _limit_chunks_per_doc(
        docs: List[Dict[str, Any]],
        max_per_doc: int,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Limit number of chunks per document to avoid one-doc overrepresentation."""
        if max_per_doc <= 0:
            return docs[:top_k]

        counts: Dict[str, int] = {}
        selected: List[Dict[str, Any]] = []
        for doc in docs:
            if len(selected) >= top_k:
                break
            doc_id = doc.get("metadata", {}).get("doc_id", "")
            if doc_id:
                if counts.get(doc_id, 0) >= max_per_doc:
                    continue
                counts[doc_id] = counts.get(doc_id, 0) + 1
            selected.append(doc)
        return selected

    @staticmethod
    def _build_summary_prompt(doc_ids: List[str], doc_names: Dict[str, str]) -> str:
        """Build strict summary prompt with one section per unique document."""
        if len(doc_ids) <= 1:
            return (
                "Provide a comprehensive summary and overview of this document. "
                "Cover the main topics, purpose, and key points."
            )

        ordered_names = [doc_names.get(doc_id, doc_id) for doc_id in doc_ids]
        bullet_list = "\n".join(f"- {name}" for name in ordered_names)
        return (
            "Summarize the uploaded documents using EXACTLY one section per unique filename.\n"
            "Output requirements:\n"
            f"- Create exactly {len(ordered_names)} sections, one for each filename below.\n"
            "- Use this heading format exactly once per file: `### <filename>`.\n"
            "- Do NOT split one document into multiple sections based on page numbers or excerpts.\n"
            "- Each section should be 2-4 concise sentences.\n"
            "- After all sections, add a short `### Connections` section with shared themes.\n\n"
            "Filenames:\n"
            f"{bullet_list}"
        )

    async def answer(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate an answer with sources and entities.

        Args:
            query: User's question
            user_id: User ID for multi-tenant isolation
            chat_history: Previous conversation messages for follow-up context
            doc_ids: List of document IDs to filter by (empty/None = all documents)
        """
        normalized_doc_ids = self._normalize_doc_ids(doc_ids)
        cache_key = self._build_response_cache_key(query, user_id, normalized_doc_ids, chat_history)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.info("Response cache hit (non-stream)")
            return cached_response

        # Route query by intent
        intent = self.query_router.classify(query)

        if intent in ("greeting", "chitchat"):
            logger.info(f"Routed to casual response (intent: {intent})")
            answer = self.query_router.generate_casual_response(query, chat_history=chat_history)
            return {
                "answer": answer,
                "contexts": [],
                "sources": [],
                "entities": [],
                "reflection": None,
            }

        if intent == "summary":
            logger.info("Routed to summary pipeline")
            effective_doc_ids = self._resolve_summary_doc_ids(query, user_id, normalized_doc_ids)
            semantic_cached, semantic_embedding = await self._get_semantic_cached_response(
                query=query,
                user_id=user_id,
                doc_ids=effective_doc_ids,
                chat_history=chat_history,
                intent="summary",
            )
            if semantic_cached:
                self._set_cached_response(cache_key, semantic_cached)
                return semantic_cached
            result = await self._generate_summary(
                query,
                user_id,
                chat_history=chat_history,
                doc_ids=effective_doc_ids
            )
            self._set_cached_response(cache_key, result)
            self._set_semantic_cached_response(
                query=query,
                response=result,
                user_id=user_id,
                doc_ids=effective_doc_ids,
                chat_history=chat_history,
                intent="summary",
                query_embedding=semantic_embedding,
            )
            return result

        # Document query - full RAG pipeline
        logger.info(f"Routed to RAG pipeline (intent: {intent})")
        semantic_cached, semantic_embedding = await self._get_semantic_cached_response(
            query=query,
            user_id=user_id,
            doc_ids=normalized_doc_ids,
            chat_history=chat_history,
            intent="document_query",
        )
        if semantic_cached:
            self._set_cached_response(cache_key, semantic_cached)
            return semantic_cached

        logger.info(f"Retrieving candidates for: {query[:80]}")
        candidates = await self.retrieval.retrieve(query, user_id=user_id, doc_ids=normalized_doc_ids)
        logger.info(f"Retrieved {len(candidates)} candidates")

        # Filter out empty/low-content chunks
        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 10]
        logger.info(f"After filtering low-content: {len(candidates)} candidates")

        reranked = await self.reranker.rerank(query, candidates, settings.RERANK_TOP_K)
        reranked = self._diversify_by_doc(reranked, settings.RERANK_TOP_K, normalized_doc_ids)
        logger.info(f"Reranked to {len(reranked)} results")

        doc_names = self._build_doc_names(user_id)
        contexts, source_map = self.assembler.assemble_with_citations(reranked, doc_names=doc_names)
        logger.info(f"Assembled {len(contexts)} contexts")

        answer = self.generator.generate(query, contexts, chat_history=chat_history)
        logger.info(f"Generated answer ({len(answer)} chars)")

        # Judge evaluation
        reflection = None
        if self.answer_judge:
            verdict = self.answer_judge.evaluate(query, contexts, answer)
            if verdict.verdict == "fail" and settings.JUDGE_MAX_RETRIES > 0:
                logger.info(f"Judge failed answer (overall={verdict.overall:.2f}), regenerating with feedback...")
                answer = self.generator.generate_with_feedback(
                    query, contexts, verdict.feedback, chat_history=chat_history
                )
                logger.info(f"Regenerated answer ({len(answer)} chars)")
                verdict = self.answer_judge.evaluate(query, contexts, answer)
                verdict.was_regenerated = True
            reflection = verdict.to_dict()

        # Extract entities from the answer for graph visualization
        entities = self._extract_entities(query, answer)
        logger.info(f"Extracted {len(entities)} entities")

        response = {
            "answer": answer,
            "contexts": contexts,
            "sources": [doc.get("metadata", {}) for doc in reranked],
            "source_map": source_map,
            "entities": entities,
            "reflection": reflection,
        }
        self._set_cached_response(cache_key, response)
        self._set_semantic_cached_response(
            query=query,
            response=response,
            user_id=user_id,
            doc_ids=normalized_doc_ids,
            chat_history=chat_history,
            intent="document_query",
            query_embedding=semantic_embedding,
        )
        return response

    async def _generate_summary(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a document summary using content from early pages."""
        # Retrieve chunks from the beginning of the document (intro, abstract, TOC)
        summary_query = "introduction abstract overview purpose scope objectives table of contents"
        logger.info("Summary: retrieving intro/overview chunks...")
        candidates = await self.retrieval.retrieve(summary_query, user_id=user_id, doc_ids=doc_ids)
        logger.info(f"Summary: retrieved {len(candidates)} raw candidates")

        # Filter out empty chunks and prefer early pages
        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 10]
        candidates.sort(key=lambda c: c.get("metadata", {}).get("page", 999))

        # Use reranker for balanced multi-doc coverage
        top_candidates = await self.reranker.rerank(summary_query, candidates, settings.RERANK_TOP_K)
        top_candidates = self._diversify_by_doc(top_candidates, settings.RERANK_TOP_K, doc_ids)
        top_candidates = self._ensure_doc_coverage(top_candidates, candidates, doc_ids, settings.RERANK_TOP_K)
        if doc_ids and len(doc_ids) > 1:
            top_candidates = self._limit_chunks_per_doc(top_candidates, max_per_doc=2, top_k=settings.RERANK_TOP_K)
        logger.info(f"Summary: using {len(top_candidates)} chunks after reranking")

        if not top_candidates:
            return {
                "answer": "I couldn't find enough content to generate a summary. Try asking a specific question about the document.",
                "contexts": [],
                "sources": [],
                "entities": [],
                "reflection": None,
            }

        doc_names = self._build_doc_names(user_id)
        contexts, source_map = self.assembler.assemble_with_citations(top_candidates, doc_names=doc_names)
        logger.info(f"Summary: assembled {len(contexts)} contexts")

        covered_doc_ids: List[str] = []
        for c in top_candidates:
            did = c.get("metadata", {}).get("doc_id")
            if did and did not in covered_doc_ids:
                covered_doc_ids.append(did)
        summary_prompt = self._build_summary_prompt(covered_doc_ids, doc_names)
        answer = self.generator.generate(summary_prompt, contexts, chat_history=chat_history)
        logger.info(f"Generated summary ({len(answer)} chars)")

        # Judge evaluation
        reflection = None
        if self.answer_judge:
            verdict = self.answer_judge.evaluate(summary_prompt, contexts, answer)
            if verdict.verdict == "fail" and settings.JUDGE_MAX_RETRIES > 0:
                logger.info(f"Judge failed summary (overall={verdict.overall:.2f}), regenerating with feedback...")
                answer = self.generator.generate_with_feedback(
                    summary_prompt, contexts, verdict.feedback, chat_history=chat_history
                )
                logger.info(f"Regenerated summary ({len(answer)} chars)")
                verdict = self.answer_judge.evaluate(summary_prompt, contexts, answer)
                verdict.was_regenerated = True
            reflection = verdict.to_dict()

        entities = self._extract_entities(query, answer)

        return {
            "answer": answer,
            "contexts": contexts,
            "sources": [doc.get("metadata", {}) for doc in top_candidates],
            "source_map": source_map,
            "entities": entities,
            "reflection": reflection,
        }

    async def answer_stream(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None, doc_ids: Optional[List[str]] = None) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
        """Stream an answer as SSE events. Yields (event_type, data) tuples."""

        normalized_doc_ids = self._normalize_doc_ids(doc_ids)
        cache_key = self._build_response_cache_key(query, user_id, normalized_doc_ids, chat_history)

        # 1. Route query by intent
        yield ("status", {"stage": "routing"})
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.info("Response cache hit (stream)")
            yield ("cache", {"cache_hit": True, "cache_type": "exact"})
            if cached_response.get("sources") or cached_response.get("contexts"):
                yield ("sources", {
                    "sources": cached_response.get("sources", []),
                    "contexts": cached_response.get("contexts", []),
                    "source_map": cached_response.get("source_map", []),
                })
            yield ("status", {"stage": "generating"})
            yield ("token", {"content": cached_response.get("answer", "")})
            reflection = cached_response.get("reflection")
            if reflection:
                yield ("reflection", reflection)
            entities = cached_response.get("entities", [])
            if entities:
                yield ("status", {"stage": "extracting"})
                yield ("entities", {"entities": entities})
            yield ("done", {})
            return

        intent = await asyncio.to_thread(self.query_router.classify, query)

        if intent in ("greeting", "chitchat"):
            yield ("status", {"stage": "generating"})
            answer = await asyncio.to_thread(
                self.query_router.generate_casual_response, query, chat_history
            )
            yield ("token", {"content": answer})
            yield ("done", {})
            return

        if intent == "summary":
            effective_doc_ids = self._resolve_summary_doc_ids(query, user_id, normalized_doc_ids)
            async for event in self._generate_summary_stream(query, user_id, chat_history, effective_doc_ids):
                yield event
            return

        # 2. Retrieve
        semantic_cached, semantic_embedding = await self._get_semantic_cached_response(
            query=query,
            user_id=user_id,
            doc_ids=normalized_doc_ids,
            chat_history=chat_history,
            intent="document_query",
        )
        if semantic_cached:
            self._set_cached_response(cache_key, semantic_cached)
            yield ("cache", {"cache_hit": True, "cache_type": "semantic"})
            if semantic_cached.get("sources") or semantic_cached.get("contexts"):
                yield ("sources", {
                    "sources": semantic_cached.get("sources", []),
                    "contexts": semantic_cached.get("contexts", []),
                    "source_map": semantic_cached.get("source_map", []),
                })
            yield ("status", {"stage": "generating"})
            yield ("token", {"content": semantic_cached.get("answer", "")})
            reflection = semantic_cached.get("reflection")
            if reflection:
                yield ("reflection", reflection)
            entities = semantic_cached.get("entities", [])
            if entities:
                yield ("status", {"stage": "extracting"})
                yield ("entities", {"entities": entities})
            yield ("done", {})
            return

        yield ("cache", {"cache_hit": False, "cache_type": "none"})
        yield ("status", {"stage": "retrieving"})
        candidates = await self.retrieval.retrieve(query, user_id=user_id, doc_ids=normalized_doc_ids)
        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 10]

        # 3. Rerank
        yield ("status", {"stage": "reranking"})
        reranked = await self.reranker.rerank(query, candidates, settings.RERANK_TOP_K)
        reranked = self._diversify_by_doc(reranked, settings.RERANK_TOP_K, normalized_doc_ids)

        # 4. Assemble contexts with document labels
        doc_names = await asyncio.to_thread(self._build_doc_names, user_id)
        contexts, source_map = self.assembler.assemble_with_citations(reranked, doc_names=doc_names)
        sources = [doc.get("metadata", {}) for doc in reranked]

        # 5. Send sources before generation
        yield ("sources", {"sources": sources, "contexts": contexts, "source_map": source_map})

        # 6. Stream generation
        yield ("status", {"stage": "generating"})
        full_answer = ""
        async for token in self.generator.generate_stream(query, contexts, chat_history=chat_history):
            full_answer += token
            yield ("token", {"content": token})

        # 7. Judge evaluation
        reflection_payload = None
        if self.answer_judge:
            yield ("status", {"stage": "evaluating"})
            verdict = await asyncio.to_thread(self.answer_judge.evaluate, query, contexts, full_answer)

            if verdict.verdict == "fail" and settings.JUDGE_MAX_RETRIES > 0:
                logger.info(f"Judge failed answer (overall={verdict.overall:.2f}), regenerating...")
                yield ("status", {"stage": "improving"})
                yield ("token", {"content": "", "replace": True})

                full_answer = ""
                async for token in self.generator.generate_with_feedback_stream(
                    query, contexts, verdict.feedback, chat_history=chat_history
                ):
                    full_answer += token
                    yield ("token", {"content": token})

                verdict = await asyncio.to_thread(self.answer_judge.evaluate, query, contexts, full_answer)
                verdict.was_regenerated = True

            reflection_payload = verdict.to_dict()
            yield ("reflection", reflection_payload)

        # 8. Extract entities
        yield ("status", {"stage": "extracting"})
        entities = await asyncio.to_thread(self._extract_entities, query, full_answer)
        yield ("entities", {"entities": entities})

        self._set_cached_response(cache_key, {
            "answer": full_answer,
            "contexts": contexts,
            "sources": sources,
            "source_map": source_map,
            "entities": entities,
            "reflection": reflection_payload,
        })
        self._set_semantic_cached_response(
            query=query,
            response={
                "answer": full_answer,
                "contexts": contexts,
                "sources": sources,
                "source_map": source_map,
                "entities": entities,
                "reflection": reflection_payload,
            },
            user_id=user_id,
            doc_ids=normalized_doc_ids,
            chat_history=chat_history,
            intent="document_query",
            query_embedding=semantic_embedding,
        )

        yield ("done", {})

    async def _generate_summary_stream(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None, doc_ids: Optional[List[str]] = None) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
        """Stream a document summary as SSE events."""
        semantic_cached, semantic_embedding = await self._get_semantic_cached_response(
            query=query,
            user_id=user_id,
            doc_ids=doc_ids,
            chat_history=chat_history,
            intent="summary",
        )
        if semantic_cached:
            self._set_cached_response(
                self._build_response_cache_key(query, user_id, doc_ids, chat_history),
                semantic_cached
            )
            yield ("cache", {"cache_hit": True, "cache_type": "semantic"})
            if semantic_cached.get("sources") or semantic_cached.get("contexts"):
                yield ("sources", {
                    "sources": semantic_cached.get("sources", []),
                    "contexts": semantic_cached.get("contexts", []),
                    "source_map": semantic_cached.get("source_map", []),
                })
            yield ("status", {"stage": "generating"})
            yield ("token", {"content": semantic_cached.get("answer", "")})
            reflection = semantic_cached.get("reflection")
            if reflection:
                yield ("reflection", reflection)
            entities = semantic_cached.get("entities", [])
            if entities:
                yield ("status", {"stage": "extracting"})
                yield ("entities", {"entities": entities})
            yield ("done", {})
            return

        cache_key = self._build_response_cache_key(query, user_id, doc_ids, chat_history)
        yield ("cache", {"cache_hit": False, "cache_type": "none"})
        yield ("status", {"stage": "retrieving"})
        summary_query = "introduction abstract overview purpose scope objectives table of contents"
        candidates = await self.retrieval.retrieve(summary_query, user_id=user_id, doc_ids=doc_ids)

        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 10]
        candidates.sort(key=lambda c: c.get("metadata", {}).get("page", 999))

        # Use reranker for balanced multi-doc coverage
        yield ("status", {"stage": "reranking"})
        top_candidates = await self.reranker.rerank(summary_query, candidates, settings.RERANK_TOP_K)
        top_candidates = self._diversify_by_doc(top_candidates, settings.RERANK_TOP_K, doc_ids)
        top_candidates = self._ensure_doc_coverage(top_candidates, candidates, doc_ids, settings.RERANK_TOP_K)
        if doc_ids and len(doc_ids) > 1:
            top_candidates = self._limit_chunks_per_doc(top_candidates, max_per_doc=2, top_k=settings.RERANK_TOP_K)

        if not top_candidates:
            yield ("token", {"content": "I couldn't find enough content to generate a summary. Try asking a specific question about the document."})
            yield ("done", {})
            return

        doc_names = await asyncio.to_thread(self._build_doc_names, user_id)
        contexts, source_map = self.assembler.assemble_with_citations(top_candidates, doc_names=doc_names)
        sources = [doc.get("metadata", {}) for doc in top_candidates]
        yield ("sources", {"sources": sources, "contexts": contexts, "source_map": source_map})

        covered_doc_ids: List[str] = []
        for c in top_candidates:
            did = c.get("metadata", {}).get("doc_id")
            if did and did not in covered_doc_ids:
                covered_doc_ids.append(did)
        summary_prompt = self._build_summary_prompt(covered_doc_ids, doc_names)

        yield ("status", {"stage": "generating"})
        full_answer = ""
        async for token in self.generator.generate_stream(summary_prompt, contexts, chat_history=chat_history):
            full_answer += token
            yield ("token", {"content": token})

        # Judge evaluation
        reflection_payload = None
        if self.answer_judge:
            yield ("status", {"stage": "evaluating"})
            verdict = await asyncio.to_thread(self.answer_judge.evaluate, summary_prompt, contexts, full_answer)

            if verdict.verdict == "fail" and settings.JUDGE_MAX_RETRIES > 0:
                yield ("status", {"stage": "improving"})
                yield ("token", {"content": "", "replace": True})

                full_answer = ""
                async for token in self.generator.generate_with_feedback_stream(
                    summary_prompt, contexts, verdict.feedback, chat_history=chat_history
                ):
                    full_answer += token
                    yield ("token", {"content": token})

                verdict = await asyncio.to_thread(self.answer_judge.evaluate, summary_prompt, contexts, full_answer)
                verdict.was_regenerated = True

            reflection_payload = verdict.to_dict()
            yield ("reflection", reflection_payload)

        yield ("status", {"stage": "extracting"})
        entities = await asyncio.to_thread(self._extract_entities, query, full_answer)
        yield ("entities", {"entities": entities})

        self._set_cached_response(cache_key, {
            "answer": full_answer,
            "contexts": contexts,
            "sources": sources,
            "source_map": source_map,
            "entities": entities,
            "reflection": reflection_payload,
        })
        self._set_semantic_cached_response(
            query=query,
            response={
                "answer": full_answer,
                "contexts": contexts,
                "sources": sources,
                "source_map": source_map,
                "entities": entities,
                "reflection": reflection_payload,
            },
            user_id=user_id,
            doc_ids=doc_ids,
            chat_history=chat_history,
            intent="summary",
            query_embedding=semantic_embedding,
        )

        yield ("done", {})

    def _extract_entities(self, query: str, answer: str) -> List[str]:
        """Extract entities from query and answer for graph visualization."""
        combined_text = f"{query}\n{answer}"
        return self.entity_extractor.extract_entities(combined_text)
