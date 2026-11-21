from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.validation import require_message, require_session_id
from app.db.models import Document
from app.db.postgres import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    DocumentOut,
    NotebookCreate,
    NotebookOut,
    NotebookUpdate,
    SmritiChatRequest,
)
from app.schemas.document import ChunkingStrategy, UploadResponse
from app.services import memory_service, notebook_service
from app.services.chunking import chunk_text
from app.services.embedding_service import embed_texts
from app.services.orchestrator_service import orchestrator
from app.services.text_extraction import extract_text
from app.services.vector_store_service import upsert_chunks

router = APIRouter()

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def _chat(message: str, session_id: str) -> ChatResponse:
    result = orchestrator.respond(
        require_message(message),
        require_session_id(session_id),
        mode="shruti",
    )
    return ChatResponse(reply=result["answer"], mode="shruti")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return _chat(request.message, request.session_id)


@router.post("/converse", response_model=ChatResponse)
async def converse(request: ChatRequest):
    """Same as /chat. The screen posts here."""
    return _chat(request.message, request.session_id)


@router.post("/smriti/chat", response_model=ChatResponse)
async def smriti_chat(request: SmritiChatRequest, db: Session = Depends(get_db)):
    notebook_service.get_notebook(db, request.notebook_id)
    result = orchestrator.respond(
        require_message(request.message),
        require_session_id(request.session_id),
        mode="smriti",
        notebook_id=request.notebook_id,
    )
    return ChatResponse(reply=result["answer"], mode="smriti", citations=result["citations"])


@router.get("/conversations")
async def list_conversations():
    return memory_service.list_chat_threads()


@router.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    require_session_id(thread_id)
    return memory_service.get_thread_messages(thread_id)


@router.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    require_session_id(thread_id)
    deleted = memory_service.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation '{thread_id}' not found")
    return {"status": "deleted", "thread_id": thread_id}


@router.post("/notebooks", response_model=NotebookOut, status_code=201)
async def create_notebook(request: NotebookCreate, db: Session = Depends(get_db)):
    return notebook_service.create_notebook(db, request.title)


@router.get("/notebooks", response_model=list[NotebookOut])
async def list_notebooks(db: Session = Depends(get_db)):
    return notebook_service.list_notebooks(db)


@router.get("/notebooks/{notebook_id}", response_model=NotebookOut)
async def get_notebook(notebook_id: int, db: Session = Depends(get_db)):
    return notebook_service.notebook_payload(notebook_service.get_notebook(db, notebook_id))


@router.patch("/notebooks/{notebook_id}", response_model=NotebookOut)
async def rename_notebook(notebook_id: int, request: NotebookUpdate, db: Session = Depends(get_db)):
    return notebook_service.rename_notebook(db, notebook_id, request.title)


@router.delete("/notebooks/{notebook_id}")
async def delete_notebook(notebook_id: int, db: Session = Depends(get_db)):
    notebook_service.delete_notebook(db, notebook_id)
    return {"status": "deleted", "notebook_id": notebook_id}


@router.get("/notebooks/{notebook_id}/conversations")
async def list_notebook_conversations(notebook_id: int, db: Session = Depends(get_db)):
    notebook_service.get_notebook(db, notebook_id)
    return memory_service.list_notebook_threads(notebook_id)


@router.get("/notebooks/{notebook_id}/documents", response_model=list[DocumentOut])
async def list_documents(notebook_id: int, db: Session = Depends(get_db)):
    return notebook_service.list_documents(db, notebook_id)


@router.delete("/notebooks/{notebook_id}/documents/{document_id}")
async def delete_document(notebook_id: int, document_id: int, db: Session = Depends(get_db)):
    notebook_service.delete_document(db, notebook_id, document_id)
    return {"status": "deleted", "document_id": document_id}


@router.post("/notebooks/{notebook_id}/documents", response_model=UploadResponse)
async def upload_document(
    notebook_id: int,
    file: UploadFile = File(...),
    chunking_strategy: ChunkingStrategy = Form(ChunkingStrategy.recursive),
    db: Session = Depends(get_db),
):
    notebook_service.get_notebook(db, notebook_id)
    filename = Path(file.filename or "").name
    if not filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File is larger than 15 MB")

    try:
        text = extract_text(filename, content)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Text files must be UTF-8") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    chunks = chunk_text(text, strategy=chunking_strategy)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found. Scanned pages need a text layer.",
        )

    embeddings = embed_texts(chunks)
    document = Document(
        notebook_id=notebook_id,
        filename=filename,
        chunking_strategy=chunking_strategy.value,
        chunk_count=len(chunks),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    upsert_chunks(notebook_id, document.id, filename, chunks, embeddings)
    return UploadResponse(
        document_id=document.id,
        notebook_id=notebook_id,
        filename=filename,
        chunk_count=len(chunks),
        chunking_strategy=chunking_strategy,
    )
