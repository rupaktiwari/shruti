from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Document, Notebook
from app.services import memory_service
from app.services.vector_store_service import delete_document_points, delete_notebook_points


def clean_title(title: str | None) -> str:
    cleaned = " ".join((title or "").split())
    return cleaned[:120] or "Untitled notebook"


def notebook_payload(notebook: Notebook) -> dict:
    created = notebook.created_at.isoformat() if notebook.created_at else None
    return {
        "id": notebook.id,
        "title": notebook.title,
        "document_count": len(notebook.documents),
        "created_at": created,
    }


def document_payload(document: Document) -> dict:
    uploaded = document.uploaded_at.isoformat() if document.uploaded_at else None
    return {
        "id": document.id,
        "notebook_id": document.notebook_id,
        "filename": document.filename,
        "chunk_count": document.chunk_count,
        "chunking_strategy": document.chunking_strategy,
        "uploaded_at": uploaded,
    }


def get_notebook(db: Session, notebook_id: int) -> Notebook:
    notebook = db.get(Notebook, notebook_id)
    if notebook is None:
        raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found")
    return notebook


def list_notebooks(db: Session) -> list[dict]:
    rows = db.query(Notebook).order_by(Notebook.id.desc()).all()
    return [notebook_payload(row) for row in rows]


def create_notebook(db: Session, title: str | None) -> dict:
    notebook = Notebook(title=clean_title(title))
    db.add(notebook)
    db.commit()
    db.refresh(notebook)
    return notebook_payload(notebook)


def rename_notebook(db: Session, notebook_id: int, title: str) -> dict:
    notebook = get_notebook(db, notebook_id)
    notebook.title = clean_title(title)
    db.commit()
    db.refresh(notebook)
    return notebook_payload(notebook)


def delete_notebook(db: Session, notebook_id: int) -> None:
    notebook = get_notebook(db, notebook_id)
    delete_notebook_points(notebook_id)
    memory_service.delete_notebook_threads(notebook_id)
    db.delete(notebook)
    db.commit()


def list_documents(db: Session, notebook_id: int) -> list[dict]:
    get_notebook(db, notebook_id)
    rows = (
        db.query(Document)
        .filter(Document.notebook_id == notebook_id)
        .order_by(Document.id.asc())
        .all()
    )
    return [document_payload(row) for row in rows]


def delete_document(db: Session, notebook_id: int, document_id: int) -> None:
    get_notebook(db, notebook_id)
    document = db.get(Document, document_id)
    if document is None or document.notebook_id != notebook_id:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    delete_document_points(document_id)
    db.delete(document)
    db.commit()
