import torch
import librosa
from silero_vad import load_silero_vad, get_speech_timestamps

class VADService:
    def __init__(self, sampling_rate: int = 16000):
        self.model = load_silero_vad(onnx=True)
        self.sampling_rate = sampling_rate

    def trim_silence(self, audio_path: str):
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