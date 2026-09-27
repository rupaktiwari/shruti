from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.tts_service import tts_service


tts_router = APIRouter()


class TTSRequest(BaseModel):
    text: str


@tts_router.post("/tts", response_class=Response)
async def synthesize_speech(request: TTSRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    audio_bytes = tts_service.synthesize(text)

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
    )