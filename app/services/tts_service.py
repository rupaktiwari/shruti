from io import BytesIO

import soundfile as sf
import torch
from transformers import AutoTokenizer, VitsModel


MODEL_NAME = "facebook/mms-tts-hin"


class TTSService:
    def __init__(self):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.tokenizer = None
        self.model = None

    def _load_model(self):
        if self.model is not None:
            return

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = VitsModel.from_pretrained(MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()

    def synthesize(self, text: str) -> bytes:
        text = text.strip()
        if not text:
            raise ValueError("TTS text cannot be empty.")

        self._load_model()

        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = inputs.to(self.device)

        with torch.inference_mode():
            waveform = self.model(**inputs).waveform

        audio = waveform.squeeze(0).cpu().numpy()

        buffer = BytesIO()
        sf.write(
            buffer,
            audio,
            self.model.config.sampling_rate,
            format="WAV",
            subtype="PCM_16",
        )
        return buffer.getvalue()


tts_service = TTSService()