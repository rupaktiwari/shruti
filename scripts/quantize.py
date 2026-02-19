# scripts/quantize.py
import os
import warnings
import torch
from transformers import AutoModelForCTC, AutoProcessor

# Silence warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

MODEL_ID = "wandererupak/Wav2Vec2-BERT-Nepali-ASR-Finetuned-OSLR54"
OUTPUT_DIR = "quantized_shruti_model"

def quantize_model():
    print(f"⬇️  Loading original model: {MODEL_ID}...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForCTC.from_pretrained(MODEL_ID)
    
    print(f"📉 Original size: {model.get_memory_footprint() / 1e6:.2f} MB")
    print("🔨 Quantizing model (Float32 -> Int8)...")

    # Quantize
    quantized_model = torch.quantization.quantize_dynamic(
        model, 
        {torch.nn.Linear},
        dtype=torch.qint8
    )

    print(f"📉 Quantized size: {quantized_model.get_memory_footprint() / 1e6:.2f} MB")
    print(f"💾 Saving to folder: {OUTPUT_DIR}...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Save the Model Weights (The "Engine") using standard Torch
    model_path = os.path.join(OUTPUT_DIR, "quantized_model.pt")
    torch.save(quantized_model, model_path)
    
    # 2. Save the Processor (The "Translator") using Transformers
    processor.save_pretrained(OUTPUT_DIR)
    
    print("✅ Done! Saved as 'quantized_model.pt'")

if __name__ == "__main__":
    quantize_model()