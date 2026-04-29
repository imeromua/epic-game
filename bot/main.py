import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from loguru import logger
import sys

from bot.core.config import bot_settings
from bot.handlers import player, quest, admin_handlers
from bot.middlewares.db_middleware import DbMiddleware


async def main():
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:HH:mm:ss} | {level} | {message}",
        level="INFO",
        colorize=True,
    )

    bot = Bot(
        token=bot_settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Мідлвеар
    dp.update.middleware(DbMiddleware())

    # Роутери
    dp.include_router(admin_handlers.router)
    dp.include_router(quest.router)
    dp.include_router(player.router)

    logger.info("🤖 EpicTeam Drive Bot запущено")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
