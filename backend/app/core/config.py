from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "DocChat Advanced RAG"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "gcp-starter"
    PINECONE_INDEX_NAME: str = "docgraph-multimodal"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password123"

    # OpenAI
    OPENAI_API_KEY: str

    # AWS S3 (Optional - can use local storage)
    AWS_ACCESS_KEY_ID: str = "not_required"
    AWS_SECRET_ACCESS_KEY: str = "not_required"
    AWS_BUCKET_NAME: str = "local_storage"
    AWS_REGION: str = "us-east-1"
    USE_LOCAL_STORAGE: bool = True
    LOCAL_STORAGE_PATH: str = "./uploaded_files"

    # API Settings
    CORS_ORIGINS: list = ["*"]
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # RAG Settings
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    LLM_MODEL: str = "gpt-4"
    VISION_MODEL: str = "gpt-4-vision-preview"
    TEMPERATURE: float = 0.7

    # Chunking Settings
    PARENT_CHUNK_SIZE: int = 1500
    PARENT_CHUNK_OVERLAP: int = 200
    CHILD_CHUNK_SIZE: int = 300
    CHILD_CHUNK_OVERLAP: int = 50

    # Retrieval Settings
    SEMANTIC_TOP_K: int = 10
    GRAPH_MAX_DEPTH: int = 2
    BM25_TOP_K: int = 5
    RERANK_TOP_K: int = 5

    class Config:
        env_file = [".env", str(Path(__file__).resolve().parents[3] / ".env")]
        case_sensitive = True


# Global settings instance
settings = Settings()
