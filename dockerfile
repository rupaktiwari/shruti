# 1. Base Image: Lightweight Python
FROM python:3.11-slim

# 2. Install System Dependencies (ffmpeg is required for librosa audio processing)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 3. Install uv (MUST happen before we use uv)
RUN pip install uv

# 4. Set the working directory inside the container
WORKDIR /app

# 5. Copy the requirements file (MUST happen before we install requirements)
COPY pyproject.toml ./

# 6. OPTIMIZED INSTALL: Force CPU-only PyTorch with correct index strategy
RUN uv pip install --system --no-cache -r pyproject.toml --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match

# 7. Copy your code AND your AI model (Happens last so code changes don't trigger a full reinstall)
COPY app/ app/
COPY quantized_shruti_model/ quantized_shruti_model/

# 8. Expose the port
EXPOSE 8000

# 9. Start the server
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]