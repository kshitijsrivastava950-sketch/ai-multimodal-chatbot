import shutil
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import UPLOAD_DIR
from backend.app.core.database import get_db
from backend.app.models.db_models import Document
from backend.app.schemas.chat_schemas import DocumentResponse
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ["pdf", "txt"]:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported for RAG ingestion.")

    file_uuid = uuid.uuid4().hex[:8]
    safe_filename = f"{file_uuid}_{file.filename}"
    saved_path = UPLOAD_DIR / safe_filename

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = RAGService.ingest_document(
        file_name=file.filename,
        file_path=str(saved_path),
        file_type=ext
    )
    return doc

@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()
