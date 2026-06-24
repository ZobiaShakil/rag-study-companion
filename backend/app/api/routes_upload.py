import logging
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.doc_processor import process_file
from app.services.embedding_service import store_chunks
from app.models.schemas import UploadResponse
from app.config import get_settings

logger = logging.getLogger("study_companion")

router = APIRouter(prefix="/upload", tags=["Upload"])

TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".pptx"}


@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    settings = get_settings()

    # Validate file extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Only .pdf and .pptx allowed."
        )

    # Validate file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max allowed: {settings.max_upload_size_mb}MB."
        )

    # Save to temp location
    temp_path = TEMP_DIR / f"{uuid.uuid4()}{suffix}"
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)
        logger.info(f"Saved temp file: {temp_path}")

        # Process file into chunks
        chunks = process_file(
            str(temp_path),
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap
        )

        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="No text could be extracted from this file. It may be empty or image-based."
            )

        # Use original filename (without extension) as collection name
        collection_name = Path(file.filename).stem.lower().replace(" ", "_")

        # Store in ChromaDB
        chunks_stored = store_chunks(chunks, collection_name)

        return UploadResponse(
            message="File processed and stored successfully",
            filename=file.filename,
            chunks_stored=chunks_stored,
            collection_name=collection_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    finally:
        # Always clean up temp file
        if temp_path.exists():
            temp_path.unlink()
            logger.info(f"Cleaned up temp file: {temp_path}")