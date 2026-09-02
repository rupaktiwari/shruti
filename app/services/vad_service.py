import torch
import librosa
from silero_vad import load_silero_vad, get_speech_timestamps, VADIterator

class VADService:
    def __init__(self, sampling_rate: int = 16000):
        self.model = load_silero_vad(onnx=True)
        self.sampling_rate = sampling_rate

    def trim_silence(self, audio_path: str):
        # unchanged — batch mode for file uploads
        audio, _ = librosa.load(audio_path, sr=self.sampling_rate)
        wav = torch.from_numpy(audio)

        timestamps = get_speech_timestamps(
            wav, self.model,
            sampling_rate=self.sampling_rate,
            threshold=0.5,
            speech_pad_ms=250,
        )

        if not timestamps:
            return None

        start = timestamps[0]["start"]
        end = timestamps[-1]["end"]
        return wav[start:end]

    def create_session_iterator(self) -> VADIterator:
        """One of these per connected WebSocket client — keeps that
        user's speech/silence state isolated from everyone else's."""
        return VADIterator(
            self.model,
            threshold=0.5,
            sampling_rate=self.sampling_rate,
            min_silence_duration_ms=1500,  # pause this long → speech ended
        )

    def process_pcm_chunk(self, iterator: VADIterator, raw_pcm_bytes: bytes):
        """Feed one live audio chunk in, get a start/end/None signal back."""
        import numpy as np
        audio_int16 = np.frombuffer(raw_pcm_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        return iterator(audio_float32, return_seconds=True)