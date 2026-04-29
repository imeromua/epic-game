from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    BOT_TOKEN: str
    MINIAPP_URL: str
    GROUP_CHAT_ID: int

    # PostgreSQL
    DATABASE_URL: str
    POSTGRES_DB: str = "epicteam"
    POSTGRES_USER: str = "epicteam_user"
    POSTGRES_PASSWORD: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 днів

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = []

    # Scheduler
    TIMEZONE: str = "Europe/Kyiv"

    # Ліміти
    MAX_QUESTS_PER_DAY: int = 5
    LEGENDARY_BUDGET_RESERVE: int = 440


settings = Settings()
