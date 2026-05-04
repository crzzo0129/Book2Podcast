import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    TTS_MALE_VOICE: str = "zh-CN-YunyangNeural"
    TTS_MALE_STYLE: str = "newscast"
    TTS_MALE_RATE: float = 0.95

    TTS_FEMALE_VOICE: str = "zh-CN-XiaoxiaoNeural"
    TTS_FEMALE_STYLE: str = "chat"
    TTS_FEMALE_RATE: float = 1.0

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./podcast.db")
    UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "uploads")
    AUDIO_DIR: str = os.path.join(os.path.dirname(__file__), "audio")
    STATIC_URL_PREFIX: str = "/static"

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    MAX_CHAPTER_TOKENS: int = 6000

    class Config:
        env_file = ".env"


settings = Settings()
