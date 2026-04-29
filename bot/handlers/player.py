from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart
import httpx

from bot.core.config import bot_settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, api: httpx.AsyncClient):
    tg_user = message.from_user
    name = tg_user.full_name or tg_user.username or str(tg_user.id)

    # Відкриваємо MiniApp кнопкою — реєстрація відбувається у MiniApp
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Відкрити EpicTeam Drive",
                    web_app=WebAppInfo(url=bot_settings.MINIAPP_URL),
                )
            ]
        ]
    )

    await message.answer(
        f"👋 <b>Привіт, {name}!</b>\n\n"
        f"🎯 Добро заповалувати в <b>EpicTeam Drive</b> — "
        f"платформу корпоративної гейміфікації!\n\n"
        f"⭐ Виконуй квести, збирай XP і вигравай призи!\n"
        f"📸 Фотофіксуй прострочені товари\n"
        f"🏆 Змагайся в ТОП-12 команди!",
        reply_markup=keyboard,
    )


@router.message(F.text == "/profile")
async def cmd_profile(message: Message, api: httpx.AsyncClient):
    """Команда /profile — швидка видача статистики без MiniApp"""
    tg_id = message.from_user.id

    try:
        resp = await api.get(f"/players/by-tg/{tg_id}")
        if resp.status_code == 200:
            p = resp.json()
            rank_stars = "⭐" * min(p["rank"] if isinstance(p["rank"], int) else 1, 4)
            await message.answer(
                f"👤 <b>{p['name']}</b>\n"
                f"🏅 {p['rank_display']} {rank_stars}\n"
                f"⚡ XP: <b>{p['xp']}</b>\n"
                f"🔥 Streak: <b>{p['streak']}</b> днів\n"
                f"🏆 Перемог: <b>{p['quests_won']}</b>"
            )
        else:
            await message.answer("Реєструйся через /start")
    except Exception:
        await message.answer("Сервіс недоступний, спробуй пізніше")
