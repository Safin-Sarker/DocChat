from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "DocChat Advanced RAG"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Authentication (required — set in .env)
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # OAuth (optional)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_FRONTEND_URL: str = "http://localhost:5173"
    OAUTH_BACKEND_URL: str = "http://localhost:8001"

    # Pinecone (required — set in .env)
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "gcp-starter"
    PINECONE_INDEX_NAME: str = "docgraph-multimodal"

    # Neo4j (required — set in .env)
    NEO4J_URI: str
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # OpenAI (required — set in .env)
    OPENAI_API_KEY: str

    # AWS S3 (optional — defaults to local storage)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "local_storage"
    AWS_REGION: str = "us-east-1"
    USE_LOCAL_STORAGE: bool = True
    LOCAL_STORAGE_PATH: str = "./uploaded_files"

    # API Settings
    CORS_ORIGINS: list = ["*"]
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Owner (exempt from usage limits)
    OWNER_EMAIL: str = ""

    # Usage limits (normal users only)
    MAX_DOCUMENTS_PER_USER: int = 3
    MAX_PAGES_PER_DOCUMENT: int = 20
    MAX_QUERIES_PER_DAY: int = 15

    # Rate Limiting (values use limits library syntax, e.g. "5/minute", "100/hour")
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_OAUTH: str = "10/minute"
    RATE_LIMIT_AUTH_ME: str = "30/minute"
    RATE_LIMIT_AUTH_LOGOUT: str = "10/minute"
    RATE_LIMIT_DOCUMENTS_LIST: str = "30/minute"
    RATE_LIMIT_DOCUMENT_UPLOAD: str = "5/minute"
    RATE_LIMIT_DOCUMENT_DELETE: str = "10/minute"
    RATE_LIMIT_DOCUMENT_FILE: str = "30/minute"
    RATE_LIMIT_QUERY: str = "5/minute"
    RATE_LIMIT_QUERY_STREAM: str = "5/minute"
    RATE_LIMIT_GRAPH_RELATED: str = "20/minute"

    # Embedding
    EMBEDDING_DIMENSION: int = 1536

    # RAG Settings
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    LLM_MODEL: str = "gpt-4"
    VISION_MODEL: str = "gpt-4-vision-preview"
    TEMPERATURE: float = 0.7
    ENABLE_EMBEDDING_CACHE: bool = True
    EMBEDDING_CACHE_TTL_SECONDS: int = 60 * 60 * 24
    EMBEDDING_CACHE_MAX_SIZE: int = 20000
    ENABLE_QUERY_RESPONSE_CACHE: bool = True
    QUERY_RESPONSE_CACHE_TTL_SECONDS: int = 60 * 15
    QUERY_RESPONSE_CACHE_MAX_SIZE: int = 2000
    ENABLE_SEMANTIC_QUERY_CACHE: bool = True
    SEMANTIC_CACHE_SIMILARITY_THRESHOLD: float = 0.92
    SEMANTIC_CACHE_REQUIRE_EMPTY_HISTORY: bool = True

    # Chunking Settings
    PARENT_CHUNK_SIZE: int = 1500
    PARENT_CHUNK_OVERLAP: int = 200
    CHILD_CHUNK_SIZE: int = 300
    CHILD_CHUNK_OVERLAP: int = 50

    # Retrieval Settings
    SEMANTIC_TOP_K: int = 20
    GRAPH_MAX_DEPTH: int = 2
    BM25_TOP_K: int = 5
    RERANK_TOP_K: int = 10
    HYBRID_MIN_PER_DOC: int = 3
    CONTEXT_SNIPPET_LENGTH: int = 200

    # Reranking
    RERANKER_RELEVANCE_THRESHOLD: float = 0.75
    RERANKER_DOC_GAP_THRESHOLD: float = 0.05

    # Query Router
    QUERY_ROUTER_MODEL: str = "gpt-4o-mini"
    QUERY_ROUTER_TEMPERATURE: float = 0.0

    # Graph Builder
    GRAPH_BUILDER_MAX_BATCH_CHARS: int = 3000

    # Text Extraction
    TEXT_MAX_SECTION_CHARS: int = 3000

    # Judge (LLM-as-a-Judge reflection layer)
    JUDGE_ENABLED: bool = True
    JUDGE_MODEL: str = "gpt-4o-mini"
    JUDGE_TEMPERATURE: float = 0.0
    JUDGE_THRESHOLD: float = 0.6
    JUDGE_MAX_RETRIES: int = 1
    JUDGE_SCORE_WEIGHTS: str = "0.30,0.25,0.20,0.15,0.10"

    class Config:
        env_file = [".env", str(Path(__file__).resolve().parents[3] / ".env")]
        case_sensitive = True


# Global settings instance
settings = Settings()
