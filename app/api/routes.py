import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.transcription import TranscriptionResponse
from app.services.ml_model import shruti_engine

router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    
    # 1. Create a temporary filename
    temp_filename = f"temp_{file.filename}"

    try:
        # 2. Save the uploaded bytes to a real file on disk
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Run Inference
        text_output = shruti_engine.predict(temp_filename)

        return TranscriptionResponse(
            filename=file.filename,
            transcription=text_output,
            model_used=shruti_engine.model_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    finally:
        # 4. Cleanup: Delete the temp file so your disk doesn't fill up
        if os.path.exists(temp_filename):
            os.remove(temp_filename)