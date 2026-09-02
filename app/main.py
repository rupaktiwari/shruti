from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import router
from app.api.ws_routes import ws_router
from app.services.ml_model import shruti_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Project Shruti is starting...")
    shruti_engine.load_model()
    yield
    print("Shutting down...")

app = FastAPI(
    title="Project Shruti API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)
app.include_router(ws_router)

@app.get("/")
def health_check():
    return {"message": "Namaste! Project Shruti is ready to listen."}