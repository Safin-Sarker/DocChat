"""Document upload endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import aiofiles
from app.schemas.document import DocumentUploadResponse, DeleteDocumentResponse
from app.services.multimodal_processor import MultimodalProcessor
from app.services.storage_service import StorageService
from app.models.pinecone_store import PineconeStore
from app.models.graph_store import GraphStore


router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    temp_dir = Path("./tmp_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"

    try:
        async with aiofiles.open(temp_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out_file.write(chunk)

        processor = MultimodalProcessor()
        result = await processor.process_document(str(temp_path), file.filename)
        return DocumentUploadResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document(doc_id: str):
    """Delete a document and all associated data."""
    errors = []

    # 1. Delete from Pinecone
    try:
        pinecone_store = PineconeStore()
        await pinecone_store.delete_by_doc_id(doc_id)
    except Exception as e:
        errors.append(f"Pinecone: {str(e)}")

    # 2. Delete from Neo4j Graph
    try:
        graph_store = GraphStore()
        graph_store.delete_by_doc_id(doc_id)
        graph_store.close()
    except Exception as e:
        errors.append(f"Graph: {str(e)}")

    # 3. Delete from Storage
    try:
        storage = StorageService()
        await storage.delete_document_files(doc_id)
    except Exception as e:
        errors.append(f"Storage: {str(e)}")

    if errors:
        return DeleteDocumentResponse(status="partial", doc_id=doc_id, errors=errors)

    return DeleteDocumentResponse(status="deleted", doc_id=doc_id)
