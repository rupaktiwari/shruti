from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    front_desk_email: str = "front-desk@himalayahouse.example"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5433/shruti"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
