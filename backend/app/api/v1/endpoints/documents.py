"""Document upload endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import aiofiles
from app.schemas.document import DocumentUploadResponse
from app.services.multimodal_processor import MultimodalProcessor


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
