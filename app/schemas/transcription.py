from pydantic import BaseModel

class TranscriptionResponse(BaseModel):
    filename: str
    transcription: str
    model_used: str

    