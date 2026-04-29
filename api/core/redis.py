import redis.asyncio as aioredis
from loguru import logger
from api.core.config import settings

# Глобальний клієнт Redis
_redis: aioredis.Redis | None = None


async def init_redis():
    global _redis
    _redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    await _redis.ping()
    logger.info("Redis підключено")


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis не ініціалізовано")
    return _redis


# ==========================================
# Redis ключі (централізовані в одному місці)
# ==========================================

class RedisKeys:
    @staticmethod
    def quest_status(quest_id: int) -> str:
        return f"quest:{quest_id}:status"

    @staticmethod
    def quest_winner(quest_id: int) -> str:
        """First-Win lock — SET NX EX"""
        return f"quest:{quest_id}:winner"

    @staticmethod
    def quest_attempts(quest_id: int, player_id: int) -> str:
        return f"quest:{quest_id}:attempts:{player_id}"

    @staticmethod
    def player_cooldown(player_id: int) -> str:
        """Pісля перемоги — не може бути 'першим' 2 годи"""
        return f"player:{player_id}:cooldown"

    @staticmethod
    def leaderboard_monthly() -> str:
        """Sorted Set — ZADD score=xp member=player_id"""
        return "leaderboard:monthly"

    @staticmethod
    def leaderboard_daily() -> str:
        return "leaderboard:daily"

    @staticmethod
    def daily_quests_count(date_str: str) -> str:
        """date_str формат YYYY-MM-DD"""
        return f"daily:quests:{date_str}"

    @staticmethod
    def bot_notification(channel: str = "main") -> str:
        return f"bot:notifications:{channel}"
