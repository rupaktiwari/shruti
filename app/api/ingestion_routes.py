from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.models import Document
from app.db.postgres import get_db
from app.schemas.document import ChunkingStrategy, UploadResponse
from app.services.chunking import chunk_text
from app.services.embedding_service import embed_texts
from app.services.text_extraction import extract_text
from app.services.vector_store_service import upsert_chunks

ingestion_router = APIRouter()


@ingestion_router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunking_strategy: ChunkingStrategy = Form(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported")

    text = extract_text(file.filename, await file.read())
    chunks = chunk_text(text, strategy=chunking_strategy)
    if not chunks:
        raise HTTPException(status_code=400, detail="No extractable text found in file")

    embeddings = embed_texts(chunks)
    document = Document(
        filename=file.filename,
        chunking_strategy=chunking_strategy.value,
        chunk_count=len(chunks),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    upsert_chunks(document.id, file.filename, chunks, embeddings)

    return UploadResponse(
        document_id=document.id,
        filename=file.filename,
        chunk_count=len(chunks),
        chunking_strategy=chunking_strategy,
    )
