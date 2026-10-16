FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv pip install \
    --system \
    --no-cache \
    -r pyproject.toml \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --index-strategy unsafe-best-match

COPY app/ app/
COPY knowledge_base/ knowledge_base/
COPY scripts/ingest_knowledge_base.py scripts/ingest_knowledge_base.py

# Bake model weights into the image at build time — no runtime network dependency.
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='wandererupak/shruti-quantized', local_dir='/app/quantized_shruti_model')"

# Build Chroma inside the image from the knowledge-base files.
RUN python scripts/ingest_knowledge_base.py

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]