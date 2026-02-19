from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import router
from app.services.ml_model import shruti_engine

# Lifespan: What happens when the app starts and stops
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("🚀 Project Shruti is starting...")
    shruti_engine.load_model() # <--- Loads the AI model here
    yield
    # --- Shutdown ---
    print("🛑 Shutting down...")

app = FastAPI(
    title="Project Shruti API",
    version="1.0.0",
    lifespan=lifespan
)

# Connect our router to the app
app.include_router(router)

@app.get("/")
def health_check():
    return {"message": "Namaste! Project Shruti is ready to listen."}