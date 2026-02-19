"""Document upload endpoints."""

import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
import uuid
import aiofiles
import mimetypes

logger = logging.getLogger(__name__)
from app.schemas.document import DocumentUploadResponse, DeleteDocumentResponse, DocumentInfo
from app.services.multimodal_processor import MultimodalProcessor
from app.services.storage_service import StorageService
from app.models.pinecone_store import PineconeStore
from app.models.graph_store import GraphStore
from app.models.document import Document
from app.core.auth import get_current_user
from app.core.config import settings


router = APIRouter()

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".pptx": "pptx",
    ".txt": "txt",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
}

SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "text/plain": "txt",
    "image/png": "image",
    "image/jpeg": "image",
    "image/gif": "image",
}


def _detect_file_type(file: UploadFile) -> Optional[str]:
    """Normalize a supported upload type from MIME and extension."""
    content_type = (file.content_type or "").lower().strip()
    if content_type in SUPPORTED_MIME_TYPES:
        return SUPPORTED_MIME_TYPES[content_type]

    extension = Path(file.filename or "").suffix.lower()
    return SUPPORTED_EXTENSIONS.get(extension)


@router.get("/", response_model=List[DocumentInfo])
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List all documents for the current user."""
    user_id = current_user["user_id"]
    documents = Document.get_by_user(user_id)
    return documents


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and process a document (requires authentication)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    file_type = _detect_file_type(file)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Supported formats: PDF (.pdf), Word (.docx), "
                "Excel (.xlsx), PowerPoint (.pptx), Text (.txt), "
                "and images (.png, .jpg, .jpeg, .gif)."
            ),
        )

    user_id = current_user["user_id"]
    temp_dir = Path("./tmp_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"

    try:
        logger.info(f"Upload started: {file.filename} (user: {user_id})")

        async with aiofiles.open(temp_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out_file.write(chunk)

        logger.info(f"File saved to disk, starting processing: {file.filename}")

        processor = MultimodalProcessor()
        result = await processor.process_document(
            str(temp_path),
            file.filename,
            file_type=file_type,
            user_id=user_id
        )

        logger.info(f"Processing complete: {file.filename} - {result.get('pages', 0)} pages, {result.get('upserted_vectors', 0)} vectors")

        # Save document record to database
        Document.create(
            doc_id=result["doc_id"],
            user_id=user_id,
            filename=file.filename,
            pages=result.get("pages", 0)
        )

        logger.info(f"Upload finished: {file.filename}")
        return DocumentUploadResponse(**result)
    except Exception as exc:
        import traceback
        logger.error(f"Upload failed: {file.filename} - {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document and all associated data (requires authentication)."""
    user_id = current_user["user_id"]
    errors = []

    # 1. Delete from Pinecone
    try:
        pinecone_store = PineconeStore()
        await pinecone_store.delete_by_doc_id(doc_id, user_id=user_id)
    except Exception as e:
        errors.append(f"Pinecone: {str(e)}")

    # 2. Delete from Neo4j Graph
    try:
        graph_store = GraphStore()
        graph_store.delete_by_doc_id(doc_id, user_id=user_id)
        graph_store.close()
    except Exception as e:
        errors.append(f"Graph: {str(e)}")

    # 3. Delete from Storage
    try:
        storage = StorageService()
        await storage.delete_document_files(doc_id, user_id=user_id)
    except Exception as e:
        errors.append(f"Storage: {str(e)}")

    # 4. Delete from Database
    try:
        Document.delete(doc_id, user_id)
    except Exception as e:
        errors.append(f"Database: {str(e)}")

    if errors:
        return DeleteDocumentResponse(status="partial", doc_id=doc_id, errors=errors)

    return DeleteDocumentResponse(status="deleted", doc_id=doc_id)


@router.get("/{doc_id}/file")
async def get_document_file(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Stream/download the original uploaded document file."""
    user_id = current_user["user_id"]
    doc = Document.get_by_id(doc_id, user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = doc["filename"]
    media_type, _ = mimetypes.guess_type(filename)
    media_type = media_type or "application/octet-stream"

    if settings.USE_LOCAL_STORAGE:
        file_path = Path(settings.LOCAL_STORAGE_PATH) / user_id / doc_id / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Stored file not found")
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
        )

    # S3 mode: return a short-lived pre-signed URL to the object
    try:
        import boto3

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        key = f"{user_id}/{doc_id}/{filename}"
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_BUCKET_NAME, "Key": key},
            ExpiresIn=300,
        )
        return RedirectResponse(url=presigned_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document file: {exc}") from exc
