# app/api/converse_routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.orchestrator_service import orchestrator

converse_router = APIRouter()

class ConverseRequest(BaseModel):
    transcript: str
    thread_id: str

class ConverseResponse(BaseModel):
    answer: str
    route: str

@converse_router.post("/converse", response_model=ConverseResponse)
async def converse(request: ConverseRequest):
    result = orchestrator.respond(request.transcript, request.thread_id)
    return ConverseResponse(**result)
