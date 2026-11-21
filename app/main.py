from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as asr_router
from app.api.workspace_routes import router as workspace_router
from app.api.ws_routes import ws_router
from app.core.logging_config import get_logger, setup_logging
from app.db import models  # noqa: F401 — registers tables
from app.services.ml_model import shruti_engine
from app.services.schema import prepare_database
from app.services.vector_store_service import ensure_collection

logger = get_logger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Shruti is starting")
    prepare_database()
    ensure_collection()
    try:
        shruti_engine.load_model()
    except RuntimeError as exc:
        logger.warning("Voice transcription is off until the ASR model is present: %s", exc)
    yield
    logger.info("Shruti is shutting down")


app = FastAPI(
    title="Shruti",
    description="Shruti is the chat. Smriti is the notebook. Nepali speech can be used in both.",
    version="3.0.0",
    lifespan=lifespan,
)

app.include_router(asr_router)
app.include_router(ws_router)
app.include_router(workspace_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health_check():
    return {
        "message": "Namaste. Shruti is ready.",
        "asr_loaded": shruti_engine.model is not None,
        "modes": ["shruti", "smriti"],
    }
