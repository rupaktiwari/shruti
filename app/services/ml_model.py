import torch
import logging
import os
from transformers import AutoProcessor
from app.services.vad_service import VADService

logger = logging.getLogger("uvicorn")

class ShrutiModel:
    def __init__(self):
        self.model_id = "Local Quantized Wav2Vec2-BERT"
        self.model_dir = "quantized_shruti_model"
        self.model_file = "quantized_model.pt"
        self.processor = None
        self.model = None
        self.vad = VADService()

    def load_model(self):
        logger.info("💻 Loading Local Quantized Model...")
        full_model_path = os.path.join(self.model_dir, self.model_file)

        if not os.path.exists(full_model_path):
            raise RuntimeError(f"❌ Model file '{full_model_path}' not found!")

        try:
            self.processor = AutoProcessor.from_pretrained(self.model_dir)
            self.model = torch.load(full_model_path, weights_only=False)
            self.model.eval()
            logger.info("✅ Quantized Model Loaded Successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e

    def predict(self, file_path: str) -> str:
        if not self.model or not self.processor:
            raise RuntimeError("Model is not loaded.")

        trimmed_audio = self.vad.trim_silence(file_path)
        if trimmed_audio is None:
            logger.info("🔇 No speech detected — skipping ASR inference.")
            return ""

        audio_input = trimmed_audio.numpy()

        inputs = self.processor(
            audio_input,
            return_tensors="pt",
            sampling_rate=16000
        )

        if "input_features" in inputs:
            model_inputs = inputs.input_features
        else:
            model_inputs = inputs.input_values

        with torch.no_grad():
            logits = self.model(model_inputs).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]

        return transcription

shruti_engine = ShrutiModel()