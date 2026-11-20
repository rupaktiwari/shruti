from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.converse_routes import converse_router
from app.api.ingestion_routes import ingestion_router
from app.api.routes import router as asr_router
from app.api.ws_routes import ws_router
from app.core.logging_config import get_logger, setup_logging
from app.db import models  # noqa: F401 — registers tables
from app.db.postgres import Base, engine
from app.services.knowledge_seed import seed_knowledge_base
from app.services.ml_model import shruti_engine
from app.services.vector_store_service import ensure_collection

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Shruti is starting")
    Base.metadata.create_all(bind=engine)
    ensure_collection()
    seeded = seed_knowledge_base()
    if seeded:
        logger.info("Seeded %s resort knowledge chunks", seeded)
    try:
        shruti_engine.load_model()
    except RuntimeError as exc:
        logger.warning("Voice transcription is off until the ASR model is present: %s", exc)
    yield
    logger.info("Shruti is shutting down")


app = FastAPI(
    title="Shruti",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(asr_router)
app.include_router(ws_router)
app.include_router(converse_router)
app.include_router(ingestion_router)


@app.get("/")
def health_check():
    return {
        "message": "Namaste. Shruti is ready.",
        "asr_loaded": shruti_engine.model is not None,
    }
