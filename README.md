<p align="center">
  <img src="https://img.icons8.com/fluency/96/chat.png" alt="DocChat Logo" width="80"/>
</p>

<h1 align="center">DocChat Advanced RAG</h1>

<p align="center">
  <strong>Multimodal Document Intelligence Platform</strong>
</p>

<p align="center">
  <a href="#tech-stack"><img src="https://img.shields.io/badge/Python-3.11+-green" alt="Python"></a>
  <a href="#tech-stack"><img src="https://img.shields.io/badge/React-19.x-61DAFB" alt="React"></a>
  <a href="#tech-stack"><img src="https://img.shields.io/badge/FastAPI-0.110+-009688" alt="FastAPI"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"></a>
</p>

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [RAG Pipeline Deep Dive](#rag-pipeline-deep-dive)
  - [Query Routing](#1-query-routing)
  - [Caching Layer](#2-caching-layer-3-tier)
  - [Document Processing & Chunking](#3-document-processing--chunking)
  - [Hybrid Retrieval](#4-hybrid-retrieval)
  - [Reranking](#5-reranking)
  - [Context Assembly & Citations](#6-context-assembly--citations)
  - [Response Generation](#7-response-generation)
  - [Answer Judge](#8-answer-judge-quality-reflection)
  - [Entity Extraction](#9-entity-extraction)
- [Conversation Memory](#conversation-memory)
- [Authentication & Security](#authentication--security)
- [Usage Limits](#usage-limits)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration Reference](#configuration-reference)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

**DocChat** is a production-grade RAG platform that lets users upload multiple documents and chat across all of them in a single conversation. Select two, three, or more documents — DocChat retrieves and synthesizes answers from every selected source, with per-document citations so you always know where each piece of information came from.

### What Makes DocChat Powerful

**Dual-Database Hybrid Retrieval** — DocChat doesn't rely on a single retrieval strategy. It combines a **vector database (Pinecone)** for deep semantic search with a **graph database (Neo4j)** for entity-relationship traversal. Pinecone captures meaning — finding relevant chunks even when the wording differs from your query. Neo4j captures structure — surfacing related entities, concepts, and connections that pure vector search would miss. Together, they deliver retrieval quality that neither database could achieve alone.

**Multi-Document Conversations** — Users can select any combination of their uploaded documents and ask questions that span all of them. The retrieval pipeline balances results across documents (minimum 3 chunks per document), ensuring no source gets drowned out. The LLM is explicitly prompted to cover all selected documents and cite each one, making cross-document analysis effortless.

**Self-Correcting Answers** — Every response passes through an LLM-as-a-Judge that scores it on faithfulness, relevance, completeness, coherence, and conciseness. If the score falls below threshold, the answer is automatically regenerated with the judge's feedback — the user sees only the improved version.

**3-Tier Intelligent Caching** — Exact-match cache, semantic similarity cache (cosine ≥ 0.92), and embedding cache work together to deliver sub-second responses for repeat and near-duplicate queries, dramatically reducing API costs.

**Multimodal Document Processing** — Upload PDF, DOCX, XLSX, PPTX, TXT, or images. PDFs are processed for text, tables, and images with OCR fallback. Documents are chunked hierarchically (parent-child) to preserve context during retrieval.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                      │
│        React 19 · TypeScript · Vite · TailwindCSS · Redux Toolkit               │
│                                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐                          │
│  │  LoginForm   │  │ ChatContainer  │  │  Document    │                          │
│  │  (OAuth/JWT) │  │ (SSE Stream)   │  │  Manager     │                          │
│  └──────┬───────┘  └───────┬────────┘  └──────┬───────┘                          │
│         └──────────────────┼──────────────────┘                                  │
│                            │ Axios + Token Refresh Interceptor                   │
└────────────────────────────┼─────────────────────────────────────────────────────┘
                             │ HTTP/REST + SSE
┌────────────────────────────┼─────────────────────────────────────────────────────┐
│                            ▼                                                     │
│  ┌──────────────────────────────────────────────────────────────────────────┐    │
│  │                         FastAPI (Uvicorn)                                │    │
│  │   ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌────────┐              │    │
│  │   │ Auth API │  │Query API │  │Document API│  │Audit   │              │    │
│  │   │ /auth/*  │  │/query/*  │  │  /docs/*   │  │/audit/*│              │    │
│  │   └──────────┘  └────┬─────┘  └────────────┘  └────────┘              │    │
│  └───────────────────────┼─────────────────────────────────────────────────┘    │
│                          │                                                       │
│  ┌───────────────────────┼──────────────────────────────────────────────────┐    │
│  │                  RAG PIPELINE                                            │    │
│  │                       ▼                                                  │    │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │    │
│  │  │Query Router │→ │ 3-Tier   │→ │ Hybrid   │→ │Reranker  │             │    │
│  │  │(Intent)     │  │ Cache    │  │Retrieval │  │(Cosine)  │             │    │
│  │  └─────────────┘  └──────────┘  └──────────┘  └────┬─────┘             │    │
│  │                                                      │                   │    │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌─────▼─────┐            │    │
│  │  │Entity       │← │ Answer   │← │Response  │← │ Context   │            │    │
│  │  │Extractor    │  │ Judge    │  │Generator │  │ Assembler │            │    │
│  │  └─────────────┘  └──────────┘  └──────────┘  └───────────┘            │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
│                          BACKEND (Python)                                        │
└──────────┬───────────────┬────────────────────┬──────────────────────────────────┘
           │               │                    │
           ▼               ▼                    ▼
    ┌─────────────┐  ┌──────────┐        ┌──────────┐
    │  Pinecone   │  │  Neo4j   │        │  OpenAI  │
    │ (Vectors)   │  │ (Graph)  │        │  (LLM)   │
    │ cosine/1536 │  │ Entities │        │ GPT-4    │
    └─────────────┘  └──────────┘        └──────────┘
```

**Multi-tenancy**: All vectors and documents are scoped by `user_id`. Users can only query their own data.

---

## RAG Pipeline Deep Dive

The RAG pipeline is the core of DocChat. Every query flows through **9 stages**, orchestrated by `advanced_rag.py`.

```
User Query
    │
    ▼
┌─────────────────┐     greeting/chitchat    ┌─────────────────┐
│  1. Query       │ ──────────────────────→  │  Direct LLM     │
│     Router      │                          │  Response        │
└────────┬────────┘                          └─────────────────┘
         │ document_query / summary
         ▼
┌─────────────────┐     cache hit            ┌─────────────────┐
│  2. Cache       │ ──────────────────────→  │  Cached Response │
│     Lookup      │                          │  (exact/semantic)│
└────────┬────────┘                          └─────────────────┘
         │ cache miss
         ▼
┌─────────────────┐
│  3. Hybrid      │──→ Pinecone (semantic, top-k=20)
│     Retrieval   │──→ Neo4j (graph traversal, depth=2)
│                 │──→ Query Expansion (LLM variations)
└────────┬────────┘
         ▼
┌─────────────────┐
│  4. Reranking   │  cosine similarity ≥ 0.75, balanced per-doc
└────────┬────────┘
         ▼
┌─────────────────┐
│  5. Context     │  parent-child merge, numbered citations [1][2]
│     Assembly    │
└────────┬────────┘
         ▼
┌─────────────────┐
│  6. Response    │  GPT-4, streaming (SSE) or synchronous
│     Generation  │
└────────┬────────┘
         ▼
┌─────────────────┐     score < 0.60         ┌─────────────────┐
│  7. Answer      │ ──────────────────────→  │  Re-generate    │
│     Judge       │                          │  with feedback   │
└────────┬────────┘                          └────────┬────────┘
         │ pass (≥ 0.60)                              │
         ▼                                            ▼
┌─────────────────┐
│  8. Entity      │  NER → stored for future queries
│     Extraction  │
└────────┬────────┘
         ▼
    Final Response (answer + citations + sources + reflection scores)
```

---

### 1. Query Routing

**Service**: `query_router.py` | **Model**: `gpt-4o-mini` | **Temperature**: 0.0

The router classifies every incoming query into one of four intents:

| Intent | Action | Example |
|--------|--------|---------|
| `greeting` | Direct LLM response, no retrieval | "Hello", "Hi there" |
| `chitchat` | Direct LLM response, no retrieval | "How are you?", "Tell me a joke" |
| `summary` | Full RAG pipeline (summary-optimized prompt) | "Summarize this document" |
| `document_query` | Full RAG pipeline | "What are the safety requirements?" |

On classification failure, the router defaults to `document_query` to avoid dropping legitimate queries.

---

### 2. Caching Layer (3-Tier)

DocChat uses three independent cache tiers to minimize redundant LLM calls and embedding computations:

| Tier | Key Strategy | TTL | Max Size | Hit Condition |
|------|-------------|-----|----------|---------------|
| **Exact Response Cache** | SHA-256 of `(query + doc_ids + intent)` | 15 min | 2,000 entries | Identical query text |
| **Semantic Cache** | Embedding cosine similarity | LRU eviction | LRU OrderedDict | Cosine similarity ≥ 0.92 |
| **Embedding Cache** | Text string hash | 24 hours | 20,000 entries | Same text chunk |

**Semantic cache** is scoped by user, intent, and document set. It only activates when `chat_history` is empty (configurable via `SEMANTIC_CACHE_REQUIRE_EMPTY_HISTORY`), since conversational context changes the expected answer.

All caches use a thread-safe `TTLCache` implementation with LRU eviction at capacity.

---

### 3. Document Processing & Chunking

**Service**: `chunking_service.py`, `document_processor.py`, format-specific extractors

**Supported formats**:

| Format | Extractor | Features |
|--------|-----------|----------|
| PDF | `multimodal_processor.py` | Text, tables, images, OCR fallback |
| DOCX | `docx_extractor.py` | Paragraphs, tables |
| XLSX | `xlsx_extractor.py` | Sheet-by-sheet extraction |
| PPTX | `pptx_extractor.py` | Slide text, tables |
| TXT | `txt_extractor.py` | Plain text |
| Images (PNG, JPG, GIF) | `ocr_service.py` | Tesseract OCR |

**Hierarchical chunking strategy**:

```
Document Page
    │
    ▼
┌──────────────────────────────────────┐
│         Parent Chunk                 │  1,500 chars, 200 overlap
│  ┌────────┐ ┌────────┐ ┌────────┐   │
│  │ Child  │ │ Child  │ │ Child  │   │  300 chars, 50 overlap
│  │ Chunk  │ │ Chunk  │ │ Chunk  │   │
│  └────────┘ └────────┘ └────────┘   │
└──────────────────────────────────────┘
```

- **Child chunks** are embedded and stored in Pinecone for precise retrieval
- **Parent chunks** provide broader context during context assembly
- **Section-aware chunking** detects headers (ALL CAPS, Title Case with colon) in structured documents (CVs, specs) to preserve logical boundaries
- Each vector in Pinecone stores: `doc_id`, `page`, `text` (child), `parent_text`, `user_id`

---

### 4. Hybrid Retrieval

**Service**: `hybrid_retrieval.py`, `query_expander.py`

Retrieval combines two parallel strategies and merges results:

**Semantic Search (Pinecone)**:
- Embeds query via `text-embedding-ada-002` (1536 dimensions)
- Queries Pinecone with `top_k=20`, filtered by `user_id` and `doc_ids`
- **Query expansion**: LLM generates alternative phrasings to broaden recall
- **Multi-document balancing**: Distributes k evenly across selected documents, ensuring minimum 3 chunks per document (`HYBRID_MIN_PER_DOC`)

**Graph Traversal (Neo4j)**:
- Extracts entities from the query via NER
- Traverses entity relationships up to `max_depth=2` hops
- Returns up to 10 related entity nodes with relationship context
- Results enrich the retrieval set with structurally connected information

---

### 5. Reranking

**Service**: `reranker.py`

After hybrid retrieval, chunks are reranked using OpenAI embedding cosine similarity:

1. **Score**: Compute cosine similarity between query embedding and each chunk embedding
2. **Filter**: Drop chunks below relevance threshold (`RERANKER_RELEVANCE_THRESHOLD=0.75`)
3. **Balance**: Ensure cross-document representation — each document gets minimum allocation before remaining slots fill by score
4. **Doc gap detection**: If a document's best chunk score is more than `RERANKER_DOC_GAP_THRESHOLD=0.05` below others, flag it as potentially irrelevant
5. **Select**: Return top `RERANK_TOP_K=10` chunks

Fallback: If OpenAI embeddings fail, returns a balanced selection without scoring.

---

### 6. Context Assembly & Citations

**Service**: `context_assembler.py`

The assembler transforms ranked chunks into a structured context string for the LLM:

- **Parent-child merging**: If a child chunk was retrieved, its parent text is included for broader context
- **De-duplication**: Identical text segments are merged
- **Numbered citations**: Each context block is labeled `[1]`, `[2]`, etc.
- **Source labels**: `[Document: filename.pdf, Page 3]`
- **Source map**: Returns structured `{index, doc_name, page, text}` for frontend display

---

### 7. Response Generation

**Service**: `response_generator.py` | **Model**: `gpt-4` | **Temperature**: 0.7

The generator constructs a prompt with:
- Assembled context with citation markers
- Chat history for conversational continuity
- Multi-document guidance (instructs the LLM to cover all source documents)
- Explicit instruction to cite sources using `[1]`, `[2]` notation and to never hallucinate

**Two modes**:
- **Synchronous**: `generate()` — returns complete answer
- **Streaming (SSE)**: `generate_stream()` — yields token-by-token via Server-Sent Events

SSE events emitted during streaming:

| Event | Data | Description |
|-------|------|-------------|
| `stage` | `routing` / `retrieving` / `reranking` / `generating` / `evaluating` / `improving` / `extracting` | Pipeline progress |
| `token` | `{content, replace?}` | Incremental answer text |
| `sources` | `{sources[], contexts[], source_map[]}` | Retrieved sources |
| `cache` | `{cache_hit, cache_type}` | Cache hit notification |
| `reflection` | `ReflectionScore` | Judge evaluation |
| `done` | — | Stream complete |
| `error` | `{message}` | Error occurred |

---

### 8. Answer Judge (Quality Reflection)

**Service**: `answer_judge.py` | **Model**: `gpt-4o-mini` | **Temperature**: 0.0

The judge evaluates every generated answer across 5 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| **Faithfulness** | 30% | No hallucinations — answer is grounded in provided context |
| **Relevance** | 25% | Directly addresses the user's question |
| **Completeness** | 20% | Covers all key points from the context |
| **Coherence** | 15% | Well-structured, logical flow |
| **Conciseness** | 10% | Appropriate length, no unnecessary content |

**Scoring**: Each dimension is scored 0.0–1.0. The overall score is the weighted average.

**Verdict**:
- **Pass** (≥ 0.60): Answer is returned to the user with reflection scores
- **Fail** (< 0.60): Answer is regenerated with the judge's feedback injected into the prompt. Max `JUDGE_MAX_RETRIES=1` regeneration attempt.

The reflection scores (`faithfulness`, `relevance`, `completeness`, `coherence`, `conciseness`, `overall`, `verdict`, `feedback`, `was_regenerated`) are returned to the frontend and displayed as a quality badge.

Toggle with `JUDGE_ENABLED=true/false`.

---

### 9. Entity Extraction

**Service**: `entity_extractor.py` | **Model**: `gpt-4o-mini` | **Temperature**: 0.0

After response generation, named entities are extracted from both the query and the answer:

- **Entity types**: People, organizations, products, concepts
- Extracted entities are:
  - Stored in Neo4j as nodes with `RELATED_TO` edges (via `graph_builder.py`)
  - Scoped by `user_id` and `doc_id` for multi-tenant isolation
  - Used to enrich future queries via graph traversal

Entity extraction and judge evaluation run in **parallel** via `asyncio.gather()` for latency optimization.

---

## Conversation Memory

DocChat maintains conversational context so follow-up questions work naturally — "What about section 3?", "Can you elaborate?", "Compare that with the other document" all resolve correctly because the model sees the conversation history.

### How It Works

```
Frontend (Redux)                          Backend
┌──────────────────────┐                  ┌──────────────────────────────┐
│  messages[] store     │                  │                              │
│                       │   POST /query    │  1. Normalize history        │
│  All messages kept    │ ──────────────→  │  2. Build LLM message chain: │
│  in Redux state       │  Last 10 msgs    │     SystemMessage            │
│                       │  as chat_history  │     + HumanMessage (prev)    │
│  On each query:       │                  │     + AIMessage (prev)       │
│  - Filter empty msgs  │                  │     + HumanMessage (current  │
│  - Slice last 10      │                  │       query + contexts)      │
│  - Send {role,content}│                  │                              │
└──────────────────────┘                  └──────────────────────────────┘
```

### Sliding Window (Last 10 Messages)

The frontend sends the **last 10 non-empty messages** with each request. This keeps the prompt focused and prevents token overflow while preserving enough context for multi-turn conversations:

```
Turn 1:  User asks about safety requirements      → history: []
Turn 2:  User asks "What about compliance?"       → history: [turn1_Q, turn1_A]
Turn 3:  User asks "Compare both documents"       → history: [turn1_Q, turn1_A, turn2_Q, turn2_A]
  ...
Turn 7+: Oldest messages start sliding out         → history: [last 10 messages]
```

### Stateless Backend

The backend does **not** store conversation state. Every request carries its own history, making the system:
- **Horizontally scalable** — any backend instance can serve any request
- **Crash-resilient** — no server-side session to lose
- **Cache-friendly** — chat history is part of the cache key, so identical conversation paths return cached responses

### Memory-Aware Features

| Feature | How Memory Is Used |
|---------|-------------------|
| **Follow-up queries** | LLM sees prior Q&A pairs, resolves pronouns and references |
| **Query routing** | Greetings/chitchat router uses history for context-aware casual responses |
| **Caching** | History is included in cache keys — same question in different conversation contexts produces different cache entries |
| **Semantic cache** | Disabled when history is present (`SEMANTIC_CACHE_REQUIRE_EMPTY_HISTORY=true`) because conversational context changes the expected answer |
| **Regeneration** | On judge failure, the same history is preserved — only the failed answer is removed and regenerated |

---

## Authentication & Security

### JWT Token Flow

```
Login/Register
    │
    ▼
┌─────────────┐     ┌──────────────────┐
│ Access Token │     │  Refresh Token   │
│ HS256, 15min│     │  SHA-256, 7 days │
└──────┬──────┘     └────────┬─────────┘
       │                     │
       │  401 Expired        │  POST /auth/refresh
       │ ◄──────────────     │ ────────────────►
       │                     │
       │              ┌──────┴──────┐
       │              │  Rotation:  │
       │              │  Old token  │
       │              │  revoked,   │
       │              │  new pair   │
       │              │  issued     │
       │              └─────────────┘
```

**Refresh token rotation with theft detection**:
- Each refresh token belongs to a **token family**
- On rotation, the old token is revoked and a new one issued
- If a revoked token is reused (theft indicator), the **entire family** is revoked
- Tokens older than 30 days are cleaned up on startup and every 24 hours

**OAuth**: Google OAuth support via `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. The frontend parses the OAuth callback hash fragment and exchanges it for JWT tokens.

**Frontend interceptor**: Axios response interceptor transparently refreshes expired access tokens. Failed requests are queued and retried after refresh. On refresh failure, the user is logged out.

---

## Usage Limits

DocChat enforces per-user quotas to manage resource consumption:

| Resource | Limit | HTTP Error | Enforcement |
|----------|-------|------------|-------------|
| Documents per user | 3 | `403` | On upload |
| Pages per document | 20 | `403` | On upload |
| Queries per day | 15 | `429` | On query |

**Owner exemption**: Set `OWNER_EMAIL` in your environment. The owner account bypasses all usage limits.

**Rate limiting** (via SlowAPI):

| Endpoint | Rate |
|----------|------|
| Login | 5/min |
| Register | 3/min |
| Query | 5/min |
| Upload | 5/min |
| Delete doc | 10/min |
| Refresh token | 30/min |
| List docs / Download | 30/min |
| Graph | 20/min |

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Core language |
| **FastAPI** | Async web framework |
| **LangChain** | LLM orchestration |
| **OpenAI GPT-4** | Generation, embeddings (ada-002), vision, NER |
| **Pinecone** | Vector database (serverless, cosine, 1536d) |
| **Neo4j** | Graph database for entity relationships |
| **SQLite** | User accounts, documents, audit logs, refresh tokens |
| **SlowAPI** | Rate limiting |
| **bcrypt** | Password hashing |
| **Pydantic v2** | Settings & validation |
| **Uvicorn** | ASGI server |
| **Tesseract OCR** | Image text extraction |

### Frontend

| Technology | Purpose |
|------------|---------|
| **React 19** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool & dev server |
| **TailwindCSS** | Utility-first styling |
| **Redux Toolkit** | Global state (auth, chat, theme) |
| **RTK Query** | API data fetching |
| **Axios** | HTTP client with interceptors |
| **shadcn/ui** | Accessible component library |

### Testing

| Tool | Scope |
|------|-------|
| **pytest** | Backend unit & integration (24 test files) |
| **Vitest** | Frontend unit & integration (11 test files) |
| **Testing Library** | React component testing |

---

## Project Structure

```
DocChat/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── api.py                    # Router aggregator
│   │   │   └── endpoints/
│   │   │       ├── auth.py               # Auth & OAuth endpoints
│   │   │       ├── documents.py          # Upload, list, delete, download
│   │   │       ├── query.py              # RAG query (sync + stream)
│   │   │       └── audit.py              # Activity logging
│   │   ├── core/
│   │   │   ├── config.py                 # All settings (pydantic-settings)
│   │   │   ├── auth.py                   # Auth dependencies
│   │   │   ├── security.py               # JWT token create/verify
│   │   │   ├── limiter.py                # SlowAPI rate limiter
│   │   │   └── retry.py                  # Retry decorators
│   │   ├── models/
│   │   │   ├── database.py               # SQLite connection
│   │   │   ├── user.py                   # User CRUD (bcrypt)
│   │   │   ├── refresh_token.py          # Token rotation & theft detection
│   │   │   ├── document.py               # Document CRUD
│   │   │   ├── audit_log.py              # Audit trail
│   │   │   ├── pinecone_store.py         # Vector DB operations
│   │   │   └── graph_store.py            # Neo4j operations
│   │   ├── schemas/
│   │   │   ├── auth.py                   # Login, register, token schemas
│   │   │   ├── document.py               # Upload & document info schemas
│   │   │   └── query.py                  # Query request/response + reflection
│   │   ├── services/
│   │   │   ├── advanced_rag.py           # RAG pipeline orchestrator
│   │   │   ├── query_router.py           # Intent classification
│   │   │   ├── query_expander.py         # Query variation generation
│   │   │   ├── hybrid_retrieval.py       # Semantic + graph retrieval
│   │   │   ├── reranker.py               # Cosine similarity reranking
│   │   │   ├── context_assembler.py      # Citation-aware context building
│   │   │   ├── response_generator.py     # LLM answer generation
│   │   │   ├── answer_judge.py           # 5-dimension quality evaluation
│   │   │   ├── entity_extractor.py       # NER via OpenAI
│   │   │   ├── graph_builder.py          # Neo4j graph construction
│   │   │   ├── chunking_service.py       # Parent-child chunking
│   │   │   ├── cache_utils.py            # TTL + LRU cache utility
│   │   │   ├── document_processor.py     # Format detection & dispatch
│   │   │   ├── multimodal_processor.py   # PDF text, tables, images
│   │   │   ├── ocr_service.py            # Tesseract OCR
│   │   │   ├── storage_service.py        # Local / S3 file storage
│   │   │   ├── page_counter.py           # Page count by format
│   │   │   └── *_extractor.py            # DOCX, XLSX, PPTX, TXT, image, table
│   │   └── main.py                       # FastAPI app & lifespan
│   ├── tests/                            # 24 test files (unit + integration)
│   ├── data/                             # SQLite databases
│   ├── uploaded_files/                   # Local document storage
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── domain/                       # Business logic types
│   │   │   ├── auth/types.ts
│   │   │   ├── chat/types.ts
│   │   │   ├── document/types.ts
│   │   │   ├── query/types.ts            # SSE events, ReflectionScore
│   │   ├── infrastructure/               # API clients & state management
│   │   │   ├── api/
│   │   │   │   ├── apiClient.ts          # Axios + token refresh interceptor
│   │   │   │   ├── auth.api.ts
│   │   │   │   ├── query.api.ts
│   │   │   │   └── document.api.ts
│   │   │   └── store/
│   │   │       ├── slices/authSlice.ts   # Auth state
│   │   │       ├── slices/chatSlice.ts   # Chat messages
│   │   │       └── api/apiSlice.ts       # RTK Query
│   │   ├── application/                  # Use-case hooks
│   │   │   ├── query/useRAGQuery.ts
│   │   │   ├── query/useRAGQueryStream.ts
│   │   │   └── document/useDocumentUpload.ts
│   │   ├── presentation/                 # UI components
│   │   │   ├── features/auth/LoginForm.tsx
│   │   │   ├── features/chat/            # ChatContainer, Input, Messages, QualityBadge
│   │   │   ├── layout/
│   │   │   ├── pages/
│   │   │   └── ui/                       # shadcn/ui components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── vitest.config.ts
│   └── package.json
│
├── docker-compose.yml                    # Neo4j container
└── README.md
```

---

## Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker Desktop | Latest (for Neo4j) |

**Required API keys**: [OpenAI](https://platform.openai.com/api-keys), [Pinecone](https://www.pinecone.io/)

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/DocChat.git
cd DocChat
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Neo4j

```bash
docker-compose up -d
```

Neo4j UI: http://localhost:7474 | Bolt: `bolt://localhost:7687` | Credentials: `neo4j / password123`

### 5. Environment

Create a `.env` file in the project root (or copy from `backend/.env.example`):

```env
# ── Required ──────────────────────────────────────
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=docgraph-multimodal
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# ── Optional: Owner (bypasses usage limits) ───────
OWNER_EMAIL=admin@example.com

# ── Optional: Usage Limits ────────────────────────
MAX_DOCUMENTS_PER_USER=3
MAX_PAGES_PER_DOCUMENT=20
MAX_QUERIES_PER_DAY=15

# ── Optional: OAuth ──────────────────────────────
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
OAUTH_FRONTEND_URL=http://localhost:5173
OAUTH_BACKEND_URL=http://localhost:8001

# ── Optional: Storage ────────────────────────────
USE_LOCAL_STORAGE=True
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_BUCKET_NAME=

# ── Optional: Models ─────────────────────────────
LLM_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-ada-002
VISION_MODEL=gpt-4-vision-preview

# ── Optional: Judge ──────────────────────────────
JUDGE_ENABLED=true
JUDGE_MODEL=gpt-4o-mini
JUDGE_THRESHOLD=0.6

# ── Optional: Caching ────────────────────────────
ENABLE_EMBEDDING_CACHE=true
ENABLE_QUERY_RESPONSE_CACHE=true
ENABLE_SEMANTIC_QUERY_CACHE=true
SEMANTIC_CACHE_THRESHOLD=0.92
```

### 6. Run

```bash
# Terminal 1: Neo4j
docker-compose up

# Terminal 2: Backend
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3: Frontend
cd frontend && npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8001 |
| Swagger Docs | http://localhost:8001/api/docs |
| Neo4j Browser | http://localhost:7474 |

---

## Configuration Reference

All settings are managed in `backend/app/core/config.py` via `pydantic-settings`. Set via environment variables or `.env` file.

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me...` | JWT signing key |
| `DEBUG` | `false` | Debug mode |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `MAX_UPLOAD_SIZE` | `52428800` (50MB) | Max file upload size |

### OpenAI

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | **Required** |
| `LLM_MODEL` | `gpt-4` | Chat model |
| `VISION_MODEL` | `gpt-4-vision-preview` | Image analysis model |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | Embedding model |
| `EMBEDDING_DIMENSION` | `1536` | Embedding vector size |
| `TEMPERATURE` | `0.7` | Generation temperature |

### Pinecone

| Variable | Default | Description |
|----------|---------|-------------|
| `PINECONE_API_KEY` | — | **Required** |
| `PINECONE_ENVIRONMENT` | `gcp-starter` | Pinecone environment |
| `PINECONE_INDEX_NAME` | `docgraph-multimodal` | Index name |

### Neo4j

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | — | **Required** |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `GOOGLE_CLIENT_ID` | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth client secret |
| `OAUTH_FRONTEND_URL` | `http://localhost:5173` | OAuth redirect base |
| `OAUTH_BACKEND_URL` | `http://localhost:8001` | OAuth callback base |

### Chunking

| Variable | Default | Description |
|----------|---------|-------------|
| `PARENT_CHUNK_SIZE` | `1500` | Parent chunk size (chars) |
| `PARENT_CHUNK_OVERLAP` | `200` | Parent chunk overlap |
| `CHILD_CHUNK_SIZE` | `300` | Child chunk size (chars) |
| `CHILD_CHUNK_OVERLAP` | `50` | Child chunk overlap |

### Retrieval & Reranking

| Variable | Default | Description |
|----------|---------|-------------|
| `SEMANTIC_TOP_K` | `20` | Pinecone results per query |
| `GRAPH_MAX_DEPTH` | `2` | Neo4j traversal depth |
| `BM25_TOP_K` | `5` | BM25 results |
| `RERANK_TOP_K` | `10` | Final reranked results |
| `HYBRID_MIN_PER_DOC` | `3` | Min chunks per document |
| `CONTEXT_SNIPPET_LENGTH` | `200` | Source map snippet length |
| `RERANKER_RELEVANCE_THRESHOLD` | `0.75` | Min cosine similarity |
| `RERANKER_DOC_GAP_THRESHOLD` | `0.05` | Irrelevant doc detection gap |

### Query Router

| Variable | Default | Description |
|----------|---------|-------------|
| `QUERY_ROUTER_MODEL` | `gpt-4o-mini` | Router model |
| `QUERY_ROUTER_TEMPERATURE` | `0.0` | Router temperature |

### Caching

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_EMBEDDING_CACHE` | `true` | Enable embedding cache |
| `EMBEDDING_CACHE_TTL` | `86400` | Embedding cache TTL (24h) |
| `EMBEDDING_CACHE_MAX_SIZE` | `20000` | Max cached embeddings |
| `ENABLE_QUERY_RESPONSE_CACHE` | `true` | Enable exact response cache |
| `QUERY_RESPONSE_CACHE_TTL` | `900` | Response cache TTL (15min) |
| `QUERY_RESPONSE_CACHE_MAX_SIZE` | `2000` | Max cached responses |
| `ENABLE_SEMANTIC_QUERY_CACHE` | `true` | Enable semantic cache |
| `SEMANTIC_CACHE_THRESHOLD` | `0.92` | Min cosine similarity for hit |
| `SEMANTIC_CACHE_REQUIRE_EMPTY_HISTORY` | `true` | Only cache with no chat history |

### Answer Judge

| Variable | Default | Description |
|----------|---------|-------------|
| `JUDGE_ENABLED` | `true` | Enable quality evaluation |
| `JUDGE_MODEL` | `gpt-4o-mini` | Judge model |
| `JUDGE_TEMPERATURE` | `0.0` | Judge temperature |
| `JUDGE_THRESHOLD` | `0.6` | Pass/fail threshold |
| `JUDGE_MAX_RETRIES` | `1` | Regeneration attempts on fail |
| `JUDGE_WEIGHT_FAITHFULNESS` | `0.30` | Faithfulness weight |
| `JUDGE_WEIGHT_RELEVANCE` | `0.25` | Relevance weight |
| `JUDGE_WEIGHT_COMPLETENESS` | `0.20` | Completeness weight |
| `JUDGE_WEIGHT_COHERENCE` | `0.15` | Coherence weight |
| `JUDGE_WEIGHT_CONCISENESS` | `0.10` | Conciseness weight |

### Usage Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `OWNER_EMAIL` | — | Owner email (bypasses limits) |
| `MAX_DOCUMENTS_PER_USER` | `3` | Max documents per user |
| `MAX_PAGES_PER_DOCUMENT` | `20` | Max pages per document |
| `MAX_QUERIES_PER_DAY` | `15` | Max daily queries |

### Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LOCAL_STORAGE` | `true` | Use local filesystem |
| `LOCAL_STORAGE_PATH` | `./uploaded_files` | Local storage directory |
| `AWS_ACCESS_KEY_ID` | `not_required` | S3 access key |
| `AWS_SECRET_ACCESS_KEY` | `not_required` | S3 secret key |
| `AWS_BUCKET_NAME` | `local_storage` | S3 bucket name |
| `AWS_REGION` | `us-east-1` | S3 region |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |

---

## API Reference

All endpoints are prefixed with `/api/v1`. Full interactive docs at `/api/docs` (Swagger UI).

### Authentication — `/api/v1/auth`

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| `POST` | `/register` | Create user account | 3/min |
| `POST` | `/login` | Authenticate, get JWT + refresh token | 5/min |
| `POST` | `/refresh` | Rotate refresh token, get new token pair | 30/min |
| `GET` | `/me` | Get current user info | 30/min |
| `POST` | `/logout` | Revoke all refresh tokens | 10/min |
| `GET` | `/oauth/google` | Initiate Google OAuth flow | 10/min |
| `GET` | `/oauth/callback` | Handle OAuth callback | — |

### Documents — `/api/v1/documents`

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| `GET` | `/` | List user's documents | 30/min |
| `POST` | `/upload` | Upload & process document | 5/min |
| `DELETE` | `/{doc_id}` | Delete document + vectors | 10/min |
| `GET` | `/{doc_id}/file` | Download original file | 30/min |

### Query — `/api/v1/query`

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| `POST` | `/` | Synchronous RAG query | 5/min |
| `POST` | `/stream` | Streaming SSE RAG query | 5/min |

**Request body**: `{ query, chat_history?, doc_ids? }`

**Response**: `{ answer, contexts[], sources[], source_map[], entities[], reflection? }`

### Audit — `/api/v1/audit`

Activity logging and user action history.

### Health — `/health`

Returns dependency status for Pinecone, Neo4j, and OpenAI.

---

## Testing

### Backend (pytest)

```bash
cd backend
python -m pytest tests/ -v
```

24 test files covering:
- **Unit**: Auth, documents, query, cache, chunking, context assembly, reranking, security, usage limits, user model
- **Integration**: Full RAG pipeline, hybrid retrieval, query routing, response generation, entity extraction, storage

### Frontend (Vitest)

```bash
cd frontend
npm run test
```

11 test files covering:
- **Unit**: API client interceptors, auth/chat state slices, LoginForm, ChatInput, ChatMessages, MessageRow, DocumentList, EmptyState, UploadModal
- **Integration**: Full chat flow

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

**Guidelines**: PEP 8 for Python, TypeScript strict mode, meaningful commit messages, tests for new features.

---

## License

This project is licensed under the **MIT License**

---

## Contact

| | |
|---|---|
| **Name** | MD Safin Sarker |
| **Email** | [safinsarker1122@gmail.com](mailto:safinsarker1122@gmail.com) |
| **LinkedIn** | [linkedin.com/in/safin-sarker](https://www.linkedin.com/in/safin-sarker/) |
| **Portfolio** | [safin-portfolio-website.netlify.app](https://safin-portfolio-website.netlify.app/) |
