from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    BOT_TOKEN: str
    GROUP_CHAT_ID: int
    MINIAPP_URL: str
    API_BASE_URL: str = "http://api:8000"


bot_settings = BotSettings()
