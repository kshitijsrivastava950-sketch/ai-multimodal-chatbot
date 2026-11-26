import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media"
UPLOAD_DIR = MEDIA_DIR / "uploads"
AUDIO_OUTPUT_DIR = MEDIA_DIR / "audio"
GENERATED_IMAGE_DIR = MEDIA_DIR / "generated"

for directory in [UPLOAD_DIR, AUDIO_OUTPUT_DIR, GENERATED_IMAGE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # MySQL Database Settings
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_DB: str = os.getenv("MYSQL_DB", "chatbot_db")
    
    # SQLite Fallback Path
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "data" / "chatbot.db"))
    
    # Server Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8000))
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # Guardrails
    ENABLE_STRICT_GUARDRAILS: bool = True
    MAX_UPLOAD_SIZE_MB: int = 25

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
