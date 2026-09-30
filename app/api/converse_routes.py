from fastapi import APIRouter
from pydantic import BaseModel
from app.services.orchestrator_service import orchestrator
from app.services.conversation_log_service import conversation_log

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
    conversation_log.log_message(request.thread_id, "user", request.transcript)
    result = orchestrator.respond(request.transcript, request.thread_id, request.mode)
    conversation_log.log_message(request.thread_id, "assistant", result["answer"], result["route"])
    return ConverseResponse(**result)

@converse_router.get("/conversations")
async def list_conversations():
    return conversation_log.list_threads()

@converse_router.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    return conversation_log.get_thread_messages(thread_id)