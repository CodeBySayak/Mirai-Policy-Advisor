import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    google_api_key: str = ""
    chroma_db_dir: str = "./chroma_db"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "models/text-embedding-004"
    generation_model: str = "gemini-3.8-flash"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
