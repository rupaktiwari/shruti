# scripts/test_streaming_vad.py
import asyncio
import json
import librosa
import numpy as np
import websockets

WS_URL = "ws://127.0.0.1:8000/ws/transcribe"
TEST_FILE = "tests/test_audio.wav"
CHUNK_SAMPLES = 512


def chunk_audio(audio: np.ndarray, chunk_size: int):
    for start in range(0, len(audio), chunk_size):
        chunk = audio[start:start + chunk_size]
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        yield chunk


async def stream_test_audio():
    audio_float, sr = librosa.load(TEST_FILE, sr=16000, mono=True)

    # Append real silence so the VAD iterator has something to detect
    # AFTER your speech ends — without this, it never sees enough
    # trailing quiet to conclude the utterance is over.
    silence_padding = np.zeros(int(16000 * 1.5), dtype=np.float32)  # 1.5s
    audio_float = np.concatenate([audio_float, silence_padding])

    audio = (audio_float * 32768.0).astype(np.int16)

    async with websockets.connect(WS_URL, open_timeout=30) as ws:

        async def sender():
            for chunk in chunk_audio(audio, CHUNK_SAMPLES):
                await ws.send(chunk.tobytes())
                await asyncio.sleep(0.032)
            await asyncio.sleep(1.0)

        async def receiver():
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=15)
                print("Received:", json.loads(message))
            except asyncio.TimeoutError:
                print("No response from server within 15 seconds")

        receiver_task = asyncio.create_task(receiver())
        await sender()
        await receiver_task


asyncio.run(stream_test_audio())