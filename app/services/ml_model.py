# app/services/ml_model.py
import torch
import logging
import os
from transformers import AutoProcessor

# Setup logging
logger = logging.getLogger("uvicorn")

class ShrutiModel:
    def __init__(self):
        # --- FIX 1: Add the missing ID tag ---
        self.model_id = "Local Quantized Wav2Vec2-BERT" 
        
        self.model_dir = "quantized_shruti_model"
        self.model_file = "quantized_model.pt"
        self.processor = None
        self.model = None
        self.load_model()

    def load_model(self):
        """
        Loads the LOCAL quantized model.
        """
        logger.info("💻 Loading Local Quantized Model...")
        
        full_model_path = os.path.join(self.model_dir, self.model_file)

        if not os.path.exists(full_model_path):
            raise RuntimeError(f"❌ Model file '{full_model_path}' not found!")

        try:
            # 1. Load Processor (AutoProcessor handles the config correctly)
            self.processor = AutoProcessor.from_pretrained(self.model_dir)
            
            # 2. Load Model
            self.model = torch.load(full_model_path, weights_only=False)
            self.model.eval()
            
            # 3. No explicit engine setting (Let PyTorch Auto-Detect)
            
            logger.info("✅ Quantized Model Loaded Successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e

    def predict(self, file_path: str) -> str:
        if not self.model or not self.processor:
            raise RuntimeError("Model is not loaded.")

        import librosa 
        
        # 1. Load Audio
        audio_input, _ = librosa.load(file_path, sr=16000)

        # 2. Pre-process
        inputs = self.processor(
            audio_input, 
            return_tensors="pt", 
            sampling_rate=16000
        )

        # Handle different input types (BERT needs input_features)
        if "input_features" in inputs:
            model_inputs = inputs.input_features
        else:
            model_inputs = inputs.input_values

        # 3. Inference
        with torch.no_grad():
            logits = self.model(model_inputs).logits

        # 4. Decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]

        return transcription

# Singleton Instance
shruti_engine = ShrutiModel()