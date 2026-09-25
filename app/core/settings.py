# app/core/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    gmail_address: str = "support@example.com"

    class Config:
        env_file = ".env"

settings = Settings()