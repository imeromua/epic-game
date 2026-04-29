from pydantic_settings import BaseSettings, SettingsConfigDict


class SchedulerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    BOT_TOKEN: str
    GROUP_CHAT_ID: int
    API_BASE_URL: str = "http://api:8000"
    TIMEZONE: str = "Europe/Kyiv"

    # Вікна рандомних івентів
    RANDOM_EVENT_WINDOW_1_START: int = 8   # 08:00
    RANDOM_EVENT_WINDOW_1_END: int = 10    # 10:00
    RANDOM_EVENT_WINDOW_2_START: int = 13  # 13:00
    RANDOM_EVENT_WINDOW_2_END: int = 15    # 15:00
    MAX_RANDOM_QUESTS_PER_DAY: int = 3


sched_settings = SchedulerSettings()
