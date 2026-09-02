# app/api/ws_routes.py
import tempfile
import os
from collections import deque
import numpy as np
import soundfile as sf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ml_model import shruti_engine

ws_router = APIRouter()
SAMPLE_RATE = 16000
FRAME_SAMPLES = 512
FRAME_BYTES = FRAME_SAMPLES * 2
PRE_BUFFER_CHUNKS = 5


@ws_router.websocket("/ws/transcribe")
async def stream_transcribe(websocket: WebSocket):
    await websocket.accept()

    vad_iterator = shruti_engine.vad.create_session_iterator()
    pre_buffer = deque(maxlen=PRE_BUFFER_CHUNKS)
    audio_buffer = []
    is_speaking = False
    byte_buffer = b""

    try:
        while True:
            raw_chunk = await websocket.receive_bytes()
            byte_buffer += raw_chunk

            while len(byte_buffer) >= FRAME_BYTES:
                frame_bytes = byte_buffer[:FRAME_BYTES]
                byte_buffer = byte_buffer[FRAME_BYTES:]

                try:
                    vad_result = shruti_engine.vad.process_pcm_chunk(vad_iterator, frame_bytes)
                except ValueError as e:
                    print(f"[VAD WARNING] Skipped malformed chunk: {e}")
                    continue

                if vad_result and "start" in vad_result:
                    is_speaking = True
                    audio_buffer = list(pre_buffer)

                current_chunk = np.frombuffer(frame_bytes, dtype=np.int16)
                if is_speaking:
                    audio_buffer.append(current_chunk)
                else:
                    pre_buffer.append(current_chunk)

                if vad_result and "end" in vad_result:
                    is_speaking = False

                    full_audio = np.concatenate(audio_buffer)
                    audio_float32 = full_audio.astype(np.float32) / 32768.0

                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        sf.write(tmp.name, audio_float32, SAMPLE_RATE)
                        temp_path = tmp.name

                    try:
                        transcript = shruti_engine.predict(temp_path, skip_vad=True)
                    finally:
                        os.remove(temp_path)

                    print(f"[DEBUG] Buffered {len(full_audio)} samples ({len(full_audio)/SAMPLE_RATE:.2f}s), transcript: '{transcript}'")
                    await websocket.send_json({"event": "final_transcript", "text": transcript})

    except WebSocketDisconnect:
        print("Client disconnected from streaming session")