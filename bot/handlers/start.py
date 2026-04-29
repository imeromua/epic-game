from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx
import os

router = Router()

MINIAPP_URL = os.getenv("MINIAPP_URL", "https://your-miniapp-host.com")
API_URL     = os.getenv("API_URL", "http://api:8000")


@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    name  = message.from_user.full_name

    # Перевіряємо, чи є гравець в базі
    try:
        async with httpx.AsyncClient(base_url=API_URL, timeout=5) as client:
            r = await client.get(f"/players/by-tg/{tg_id}")
            is_new = r.status_code == 404
    except Exception:
        is_new = False

    kb = InlineKeyboardBuilder()
    kb.button(
        text="🎮 Відкрити EpicTeam Drive",
        web_app=WebAppInfo(url=MINIAPP_URL),
    )
    kb.adjust(1)

    if is_new:
        text = (
            f"Вітаємо, {name}! 🎉\n\n"
            f"Ти щойно до команди <b>EpicTeam Drive</b>.\n"
            f"Виконуй квести, збирай XP і вигравай призи! 🏆"
        )
    else:
        text = (
            f"З поверненням, {name}! 👋\n"
            f"Тисни кнопку, щоб відкрити свій профіль."
        )

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Show player profile inline"""
    tg_id = message.from_user.id
    try:
        async with httpx.AsyncClient(base_url=API_URL, timeout=5) as client:
            r = await client.get(f"/players/by-tg/{tg_id}")
        if r.status_code == 404:
            await message.answer("Ти ще не зареєстрований. Натисни /start")
            return
        p = r.json()
    except Exception:
        await message.answer("Не вдалось отримати дані.")
        return

    text = (
        f"👤 <b>{p['name']}</b>\n"
        f"🏅 Ранг: <b>{p['rank_display']}</b>\n"
        f"⭐ XP: <b>{p['xp']}</b>\n"
        f"🏆 Перемог: <b>{p['quests_won']}</b>\n"
        f"🔥 Серія: <b>{p['streak']}</b> днів\n"
        f"💎 Легендарні: <b>{p['legendary_wins']}</b>"
    )
    await message.answer(text, parse_mode="HTML")
