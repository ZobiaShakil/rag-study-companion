import logging
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.doc_processor import process_file
from app.services.embedding_service import store_chunks
from app.models.schemas import UploadResponse
from app.models.database import get_db, Subject, SubjectFile
from app.config import get_settings

logger = logging.getLogger("study_companion")
router = APIRouter(prefix="/upload", tags=["Upload"])

TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".pptx"}


@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    subject_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    settings = get_settings()

    # Validate subject exists
    subject_result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = subject_result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{suffix}'.")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f}MB).")

    temp_path = TEMP_DIR / f"{uuid.uuid4()}{suffix}"
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)

        chunks = process_file(
            str(temp_path),
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
            original_filename=file.filename
        )

        if not chunks:
            raise HTTPException(status_code=422, detail="No text could be extracted from this file.")

# Change this line in your routes_upload.py
        collection_name = f"sub_{subject_id}_{Path(file.filename).stem.lower().replace(' ', '_')}"
        store_chunks(chunks, collection_name)

        # Save file record to database
        subject_file = SubjectFile(
            subject_id=subject_id,
            filename=file.filename,
            collection_name=collection_name
        )
        db.add(subject_file)
        await db.commit()
        await db.refresh(subject_file)

        return UploadResponse(
            message="File processed and stored successfully",
            filename=file.filename,
            chunks_stored=len(chunks),
            collection_name=collection_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()