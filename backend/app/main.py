import os
import sys

# Configure Tesseract path for Windows BEFORE any other imports
if sys.platform == 'win32':
    tesseract_path = r'C:\Program Files\Tesseract-OCR'
    tesseract_exe = os.path.join(tesseract_path, 'tesseract.exe')
    if os.path.exists(tesseract_exe):
        # Add to PATH
        os.environ['PATH'] = tesseract_path + os.pathsep + os.environ.get('PATH', '')
        # Set for pytesseract
        os.environ['TESSERACT_CMD'] = tesseract_exe
        # Configure pytesseract directly
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_exe
        except ImportError:
            pass

import asyncio
import logging
import time
from contextlib import asynccontextmanager

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.core.limiter import limiter
from app.api.v1.api import api_router
from app.models.database import init_db
from app.models.refresh_token import RefreshToken

# Generate unique session ID when server starts
SERVER_SESSION_ID = str(time.time())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    cleaned = RefreshToken.cleanup_expired(days_old=30)
    if cleaned:
        logger.info("Cleaned up %d expired refresh tokens", cleaned)
    logger.info("Database initialized")

    # Launch periodic cleanup task
    async def _periodic_token_cleanup():
        while True:
            await asyncio.sleep(86400)  # 24 hours
            try:
                count = RefreshToken.cleanup_expired(days_old=30)
                if count:
                    logger.info("Periodic cleanup: removed %d expired refresh tokens", count)
            except Exception:
                logger.exception("Periodic refresh token cleanup failed")

    cleanup_task = asyncio.create_task(_periodic_token_cleanup())

    yield

    # Shutdown
    cleanup_task.cancel()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced Multimodal Graph RAG System with React Frontend",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS (added after SlowAPIMiddleware so CORS headers appear on 429 responses)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint with dependency connectivity verification."""
    dependencies = {}

    # Check Pinecone
    try:
        from app.models.pinecone_store import PineconeStore
        store = PineconeStore()
        stats = store.get_stats()
        dependencies["pinecone"] = {
            "status": "ok",
            "total_vectors": stats.get("total_vectors", 0),
        }
    except Exception as e:
        dependencies["pinecone"] = {"status": "error", "detail": str(e)}

    # Check Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        driver.verify_connectivity()
        driver.close()
        dependencies["neo4j"] = {"status": "ok"}
    except Exception as e:
        dependencies["neo4j"] = {"status": "error", "detail": str(e)}

    # Check OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        client.models.list(limit=1)
        dependencies["openai"] = {"status": "ok"}
    except Exception as e:
        dependencies["openai"] = {"status": "error", "detail": str(e)}

    all_ok = all(dep["status"] == "ok" for dep in dependencies.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "session_id": SERVER_SESSION_ID,
        "dependencies": dependencies,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DocChat Advanced RAG API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
