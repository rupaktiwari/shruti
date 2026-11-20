from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.models import Reservation
from app.db.postgres import SessionLocal
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import memory_service
from app.services.orchestrator_service import orchestrator

converse_router = APIRouter()


class ConverseRequest(BaseModel):
    transcript: str
    thread_id: str
    mode: str = "smart"


class ConverseResponse(BaseModel):
    answer: str
    route: str


@converse_router.post("/converse", response_model=ConverseResponse)
async def converse(request: ConverseRequest):
    return orchestrator.respond(request.transcript, request.thread_id, request.mode)


@converse_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = orchestrator.respond(request.message, request.session_id)
    return ChatResponse(reply=result["answer"], route=result["route"])


@converse_router.get("/conversations")
async def list_conversations():
    return memory_service.list_threads()


@converse_router.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    return memory_service.get_thread_messages(thread_id)


@converse_router.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    deleted = memory_service.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation '{thread_id}' not found")
    return {"status": "deleted", "thread_id": thread_id}


@converse_router.get("/reservations")
async def list_reservations():
    db = SessionLocal()
    try:
        rows = db.query(Reservation).order_by(Reservation.id.desc()).all()
        return [
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "check_in": row.check_in,
                "check_out": row.check_out,
                "guests": row.guests,
                "room_type": row.room_type,
            }
            for row in rows
        ]
    finally:
        db.close()
