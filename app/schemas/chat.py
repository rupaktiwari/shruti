from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: int
    filename: str
    chunk_index: int


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    mode: str = "shruti"
    citations: list[Citation] = []


class SmritiChatRequest(BaseModel):
    notebook_id: int
    session_id: str
    message: str


class NotebookCreate(BaseModel):
    title: str = Field(default="Untitled notebook", max_length=120)


class NotebookUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class NotebookOut(BaseModel):
    id: int
    title: str
    document_count: int
    created_at: str | None = None


class DocumentOut(BaseModel):
    id: int
    notebook_id: int
    filename: str
    chunk_count: int
    chunking_strategy: str
    uploaded_at: str | None = None
