from pathlib import Path

from app.db.models import Document
from app.db.postgres import SessionLocal
from app.schemas.document import ChunkingStrategy
from app.services.chunking import chunk_text
from app.services.embedding_service import embed_texts
from app.services.vector_store_service import (
    count_seed_points,
    delete_seed_points,
    upsert_chunks,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base"


def seed_knowledge_base(force: bool = False) -> int:
    """Index the resort notes in knowledge_base/ when Qdrant has no seed vectors yet."""
    if not force and count_seed_points() > 0:
        return 0
    if force:
        delete_seed_points()

    files = sorted(KNOWLEDGE_BASE.glob("*.txt"))
    if not files:
        return 0

    db = SessionLocal()
    total_chunks = 0
    try:
        for path in files:
            text = path.read_text(encoding="utf-8")
            chunks = chunk_text(text, strategy=ChunkingStrategy.recursive)
            if not chunks:
                continue
            embeddings = embed_texts(chunks)
            document = Document(
                filename=path.name,
                chunking_strategy=ChunkingStrategy.recursive.value,
                chunk_count=len(chunks),
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            upsert_chunks(document.id, path.name, chunks, embeddings, source="seed")
            total_chunks += len(chunks)
    finally:
        db.close()
    return total_chunks
