from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from loguru import logger

from scheduler.config import sched_settings


def _make_bot() -> Bot:
    return Bot(
        token=sched_settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def send_morning_digest(top: list):
    """Ранковий дайджест з ТОП-5 дня"""
    bot = _make_bot()
    try:
        lines = ["\u2600\ufe0f <b>\u0414оброго ранку! EpicTeam Drive</b>"]
        lines.append("")
        lines.append("📊 <b>ТОП-5 вчорашнього дня:</b>")

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        if top:
            for i, entry in enumerate(top[:5]):
                medal = medals[i] if i < len(medals) else f"{i+1}."
                lines.append(f"{medal} {entry['name']} — {entry['xp']} XP")
        else:
            lines.append("Чекаємо перших героїв!")

        lines.append("")
        lines.append("🎯 Сьогодні будуть рандомні квести — будь готовий! ⚡")

        await bot.send_message(
            chat_id=sched_settings.GROUP_CHAT_ID,
            text="\n".join(lines),
        )
        logger.info("Ранковий дайджест відправлено")
    finally:
        await bot.session.close()


async def send_evening_summary(top: list):
    """Вечірній підсумок з місячним рейтингом"""
    bot = _make_bot()
    try:
        lines = ["🌙 <b>Підсумок дня — EpicTeam Drive</b>"]
        lines.append("")
        lines.append("🏆 <b>Поточний ТОП-5 місяця:</b>")

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, entry in enumerate(top[:5]):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            rank = entry.get("rank_title", "")
            lines.append(
                f"{medal} {entry['name']} <i>({rank})</i> — "
                f"<b>{entry['xp']} XP</b> | 🏆{entry['quests_won']}"
            )

        lines.append("")
        lines.append("⭐ Завтра будуть нові квести! 🚀")

        await bot.send_message(
            chat_id=sched_settings.GROUP_CHAT_ID,
            text="\n".join(lines),
        )
    finally:
        await bot.session.close()


async def send_quest_announcement(quest: dict):
    """Оголошення рандомного квесту в чат"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

    bot = _make_bot()
    try:
        cat_icons = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "💎"}
        icon = cat_icons.get(quest.get("category", 1), "⭐")
        prize_line = ""
        if quest.get("prize_name"):
            prize_line = f"\n\n🎁 <b>Приз:</b> {quest.get('prize_emoji','')} {quest['prize_name']}"

        text = (
            f"🚨 <b>Рандомний квест! {icon}</b>\n\n"
            f"📌 {quest['title']}\n\n"
            f"{quest['description']}"
            f"{prize_line}\n\n"
            f"⏰ <b>Час:</b> {quest['time_limit_minutes']} хв\n"
            f"⚡ <b>XP:</b> {quest['xp_reward']}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="🎮 Відповісти!",
                    web_app=WebAppInfo(url=sched_settings.MINIAPP_URL
                        if hasattr(sched_settings, 'MINIAPP_URL') else "https://t.me"),
                )
            ]]
        )

        await bot.send_message(
            chat_id=sched_settings.GROUP_CHAT_ID,
            text=text,
            reply_markup=keyboard,
        )
    finally:
        await bot.session.close()


async def send_winner_notification(chat_id: int, winner_name: str, quest_title: str, xp: int):
    """Приватне повідомлення переможцю"""
    bot = _make_bot()
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"🏆 <b>Ви перемогли!</b>\n\n"
                f"🎯 {quest_title}\n"
                f"⚡ +<b>{xp} XP</b> нараховано!\n\n"
                f"📸 Очікуйте підтвердження від адміна..."
            ),
        )
    finally:
        await bot.session.close()
