import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo
from loguru import logger

from bot.handlers import quest as quest_handler
from bot.handlers import player as player_handler
from bot.handlers.start import router as start_router

BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://your-miniapp-host.com")


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Реєструємо роутери
    dp.include_router(start_router)
    dp.include_router(quest_handler.router)
    dp.include_router(player_handler.router)

    # Налаштовуємо Menu Button — натиснути одну кнопку і MiniApp відкриється
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🎮 EpicTeam",
            web_app=WebAppInfo(url=MINIAPP_URL),
        )
    )

    # Команди бота
    await bot.set_my_commands([
        BotCommand(command="start",   description="🌱 Головне меню"),
        BotCommand(command="profile", description="👤 Мій профіль"),
        BotCommand(command="quest",   description="⚡ Поточний квест"),
        BotCommand(command="top",     description="🏆 ТОП-12 команди"),
    ])

    logger.info("🤖 EpicTeam Drive bot стартує...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
