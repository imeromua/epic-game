from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, PhotoSize
)
from aiogram.filters import Command
import httpx

from bot.core.config import bot_settings

router = Router()


# ==========================================
# Оголошення квесту в чат (викликається з API)
# ==========================================

async def broadcast_quest(bot: Bot, quest: dict):
    """
    Надсилає повідомлення про новий квест у груповий чат.
    Викликається із scheduler або адмін-панелі.
    """
    category_icons = {
        1: "⭐",
        2: "⭐⭐",
        3: "⭐⭐⭐",
        4: "💎",
    }
    icon = category_icons.get(quest.get("category", 1), "⭐")
    prize_line = ""
    if quest.get("prize_name"):
        prize_line = f"\n\n🎁 <b>Приз:</b> {quest['prize_emoji']} {quest['prize_name']}"

    text = (
        f"🚨 <b>Новий квест! {icon}</b>\n\n"
        f"📌 {quest['title']}\n\n"
        f"{quest['description']}"
        f"{prize_line}\n\n"
        f"⏰ <b>Час:</b> {quest['time_limit_minutes']} хв\n"
        f"⚡ <b>XP:</b> {quest['xp_reward']}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Відповісти",
                    web_app=bot_settings.MINIAPP_URL,
                )
            ]
        ]
    )

    msg = await bot.send_message(
        chat_id=bot_settings.GROUP_CHAT_ID,
        text=text,
        reply_markup=keyboard,
    )
    return msg.message_id


# ==========================================
# Прийом фото в приватному чаті (фото-квест)
# ==========================================

@router.message(F.photo)
async def handle_photo_answer(message: Message, api: httpx.AsyncClient):
    """
    Гравець надсилає фото в приват. чат бота.
    Бот передає file_id на API.
    """
    # Беремо найбільше фото (останнє в списку)
    photo: PhotoSize = message.photo[-1]
    tg_id = message.from_user.id

    # Перевіряємо активний квест
    resp = await api.get("/quests/active")
    if resp.status_code != 200 or not resp.json():
        await message.answer("Наразі активних квестів немає.")
        return

    active_quest = resp.json()
    if active_quest.get("quest_type") != "photo":
        await message.answer("Поточний квест не вимагає фото.")
        return

    # Передаємо file_id на API (API сам завантажить і обрахує pHash)
    submit_resp = await api.post(
        f"/quests/photo-by-file-id",
        json={
            "quest_id": active_quest["id"],
            "tg_id": tg_id,
            "file_id": photo.file_id,
        },
    )

    if submit_resp.status_code == 200:
        data = submit_resp.json()
        await message.answer(data.get("message", "Фото отримано!"))
    else:
        await message.answer("Помилка при відправці фото. Спробуй ще раз.")
