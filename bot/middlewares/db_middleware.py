from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import httpx

from bot.core.config import bot_settings


class DbMiddleware(BaseMiddleware):
    """
    Додає httpx клієнт до кожного хендлера —
    бот звертається до FastAPI, а не прямо до БД.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with httpx.AsyncClient(base_url=bot_settings.API_BASE_URL) as client:
            data["api"] = client
            return await handler(event, data)
