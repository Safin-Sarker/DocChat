"""End-to-end RAG pipeline service."""

import asyncio
import logging
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
from app.models.document import Document


class AdvancedRAGService:
    """Orchestrate retrieval, reranking, and response generation."""

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

    async def answer(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate an answer with sources and entities.

        Args:
            query: User's question
            user_id: User ID for multi-tenant isolation
            chat_history: Previous conversation messages for follow-up context
            doc_ids: List of document IDs to filter by (empty/None = all documents)
        """
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
            return await self._generate_summary(query, user_id, chat_history=chat_history, doc_ids=doc_ids)

        # Document query - full RAG pipeline
        logger.info(f"Routed to RAG pipeline (intent: {intent})")
        logger.info(f"Retrieving candidates for: {query[:80]}")
        candidates = await self.retrieval.retrieve(query, user_id=user_id, doc_ids=doc_ids)
        logger.info(f"Retrieved {len(candidates)} candidates")

        # Filter out empty/low-content chunks
        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 10]
        logger.info(f"After filtering low-content: {len(candidates)} candidates")

        reranked = await self.reranker.rerank(query, candidates, settings.RERANK_TOP_K)
        logger.info(f"Reranked to {len(reranked)} results")

        doc_names = self._build_doc_names(user_id)
        contexts = self.assembler.assemble(reranked, doc_names=doc_names)
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

        return {
            "answer": answer,
            "contexts": contexts,
            "sources": [doc.get("metadata", {}) for doc in reranked],
            "entities": entities,
            "reflection": reflection,
        }

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
        contexts = self.assembler.assemble(top_candidates, doc_names=doc_names)
        logger.info(f"Summary: assembled {len(contexts)} contexts")

        # Detect if multi-doc or single-doc for prompt
        doc_id_set = set()
        for c in top_candidates:
            did = c.get("metadata", {}).get("doc_id")
            if did:
                doc_id_set.add(did)

        if len(doc_id_set) > 1:
            summary_prompt = (
                "Provide a comprehensive summary and overview of EACH of these documents. "
                "Summarize each document separately with its own section, then highlight any connections between them. "
                "Cover the main topics, purpose, and key points of each document."
            )
        else:
            summary_prompt = (
                "Provide a comprehensive summary and overview of this document. "
                "Cover the main topics, purpose, and key points."
            )
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
            "entities": entities,
            "reflection": reflection,
        }

    async def answer_stream(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None, doc_ids: Optional[List[str]] = None) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
        """Stream an answer as SSE events. Yields (event_type, data) tuples."""

        # 1. Route query by intent
        yield ("status", {"stage": "routing"})
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
            async for event in self._generate_summary_stream(query, user_id, chat_history, doc_ids):
                yield event
            return

        # 2. Retrieve
        yield ("status", {"stage": "retrieving"})
        candidates = await self.retrieval.retrieve(query, user_id=user_id, doc_ids=doc_ids)
        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 10]

        # 3. Rerank
        yield ("status", {"stage": "reranking"})
        reranked = await self.reranker.rerank(query, candidates, settings.RERANK_TOP_K)

        # 4. Assemble contexts with document labels
        doc_names = await asyncio.to_thread(self._build_doc_names, user_id)
        contexts = self.assembler.assemble(reranked, doc_names=doc_names)
        sources = [doc.get("metadata", {}) for doc in reranked]

        # 5. Send sources before generation
        yield ("sources", {"sources": sources, "contexts": contexts})

        # 6. Stream generation
        yield ("status", {"stage": "generating"})
        full_answer = ""
        async for token in self.generator.generate_stream(query, contexts, chat_history=chat_history):
            full_answer += token
            yield ("token", {"content": token})

        # 7. Judge evaluation
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

            yield ("reflection", verdict.to_dict())

        # 8. Extract entities
        yield ("status", {"stage": "extracting"})
        entities = await asyncio.to_thread(self._extract_entities, query, full_answer)
        yield ("entities", {"entities": entities})

        yield ("done", {})

    async def _generate_summary_stream(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None, doc_ids: Optional[List[str]] = None) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
        """Stream a document summary as SSE events."""
        yield ("status", {"stage": "retrieving"})
        summary_query = "introduction abstract overview purpose scope objectives table of contents"
        candidates = await self.retrieval.retrieve(summary_query, user_id=user_id, doc_ids=doc_ids)

        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 10]
        candidates.sort(key=lambda c: c.get("metadata", {}).get("page", 999))

        # Use reranker for balanced multi-doc coverage
        yield ("status", {"stage": "reranking"})
        top_candidates = await self.reranker.rerank(summary_query, candidates, settings.RERANK_TOP_K)

        if not top_candidates:
            yield ("token", {"content": "I couldn't find enough content to generate a summary. Try asking a specific question about the document."})
            yield ("done", {})
            return

        doc_names = await asyncio.to_thread(self._build_doc_names, user_id)
        contexts = self.assembler.assemble(top_candidates, doc_names=doc_names)
        sources = [doc.get("metadata", {}) for doc in top_candidates]
        yield ("sources", {"sources": sources, "contexts": contexts})

        # Detect if multi-doc or single-doc for prompt
        doc_id_set = set()
        for c in top_candidates:
            did = c.get("metadata", {}).get("doc_id")
            if did:
                doc_id_set.add(did)

        if len(doc_id_set) > 1:
            summary_prompt = (
                "Provide a comprehensive summary and overview of EACH of these documents. "
                "Summarize each document separately with its own section, then highlight any connections between them. "
                "Cover the main topics, purpose, and key points of each document."
            )
        else:
            summary_prompt = (
                "Provide a comprehensive summary and overview of this document. "
                "Cover the main topics, purpose, and key points."
            )

        yield ("status", {"stage": "generating"})
        full_answer = ""
        async for token in self.generator.generate_stream(summary_prompt, contexts, chat_history=chat_history):
            full_answer += token
            yield ("token", {"content": token})

        # Judge evaluation
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

            yield ("reflection", verdict.to_dict())

        yield ("status", {"stage": "extracting"})
        entities = await asyncio.to_thread(self._extract_entities, query, full_answer)
        yield ("entities", {"entities": entities})

        yield ("done", {})

    def _extract_entities(self, query: str, answer: str) -> List[str]:
        """Extract entities from query and answer for graph visualization."""
        combined_text = f"{query}\n{answer}"
        return self.entity_extractor.extract_entities(combined_text)
