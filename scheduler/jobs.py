import random
from datetime import datetime, timezone
from loguru import logger
import httpx

from scheduler.config import sched_settings
from scheduler.notifications import (
    send_morning_digest,
    send_evening_summary,
    send_quest_announcement,
)


def _now_kyiv_hour() -> int:
    """Pпоточна година в часовому поясі Києв"""
    import pytz
    tz = pytz.timezone(sched_settings.TIMEZONE)
    return datetime.now(tz).hour


def _now_kyiv() -> datetime:
    import pytz
    return datetime.now(pytz.timezone(sched_settings.TIMEZONE))


# ==========================================
# Ранковий дайджест (09:00)
# ==========================================

async def job_morning_digest():
    logger.info("Пуск ранкового дайджесту")
    try:
        async with httpx.AsyncClient(base_url=sched_settings.API_BASE_URL) as api:
            resp = await api.get("/leaderboard/daily")
            top = resp.json() if resp.status_code == 200 else []
        await send_morning_digest(top)
    except Exception as e:
        logger.error(f"Помилка ранкового дайджесту: {e}")


# ==========================================
# Вечірній підсумок (21:00)
# ==========================================

async def job_evening_summary():
    logger.info("Пуск вечірнього підсумку")
    try:
        async with httpx.AsyncClient(base_url=sched_settings.API_BASE_URL) as api:
            resp = await api.get("/leaderboard/monthly")
            top = resp.json() if resp.status_code == 200 else []
        await send_evening_summary(top)
    except Exception as e:
        logger.error(f"Помилка вечірнього підсумку: {e}")


# ==========================================
# Скидання денного лідерборду (00:01)
# ==========================================

async def job_reset_daily_leaderboard():
    logger.info("Скидання денного лідерборду")
    try:
        import redis.asyncio as aioredis
        from scheduler.config import sched_settings
        # Пряме звернення до Redis з scheduler
        import os
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = aioredis.from_url(redis_url, decode_responses=True)
        await r.delete("leaderboard:daily")
        await r.aclose()
        logger.info("Денний лідерборд скинуто")
    except Exception as e:
        logger.error(f"Помилка скидання: {e}")


# ==========================================
# Рандомні івенти (кожні 10 хв)
# ==========================================

async def job_random_event_window():
    """
    Перевіряє, чи поточна година входить у вікно.
    Вікно 08-10 або 13-15 з вірогідністю 30% запускає квест.
    """
    hour = _now_kyiv_hour()
    s = sched_settings

    in_window = (
        s.RANDOM_EVENT_WINDOW_1_START <= hour < s.RANDOM_EVENT_WINDOW_1_END
        or
        s.RANDOM_EVENT_WINDOW_2_START <= hour < s.RANDOM_EVENT_WINDOW_2_END
    )
    if not in_window:
        return

    # 30% вірогідність на кожні 10 хв
    if random.random() > 0.30:
        return

    try:
        async with httpx.AsyncClient(base_url=s.API_BASE_URL) as api:
            # Перевіряємо ліміт на день
            today = _now_kyiv().strftime("%Y-%m-%d")
            count_resp = await api.get(f"/admin/daily-quest-count?date={today}")
            count = count_resp.json().get("count", 0) if count_resp.status_code == 200 else 0

            if count >= s.MAX_RANDOM_QUESTS_PER_DAY:
                logger.info(f"Ліміт квестів за день досягнуто ({count}), пропускаємо")
            return

            # Беремо випадковий квест з шаблонів
            templates_resp = await api.get("/admin/quest-templates")
            if templates_resp.status_code != 200:
                return

            templates = templates_resp.json()
            if not templates:
                logger.warning("Немає шаблонів квестів")
                return

            template = random.choice(templates)
            quest_resp = await api.post("/admin/quests", json={
                **template,
                "start_now": True,
                "is_template": False,
            })

            if quest_resp.status_code == 200:
                quest = quest_resp.json()
                logger.info(f"Рандомний квест #{quest['id']} запущено")
                await send_quest_announcement(quest)

    except Exception as e:
        logger.error(f"Помилка рандомного івенту: {e}")


# ==========================================
# Закриття прострочених квестів (кожну хвилину)
# ==========================================

async def job_check_expired_quests():
    try:
        async with httpx.AsyncClient(base_url=sched_settings.API_BASE_URL) as api:
            resp = await api.post("/admin/expire-quests")
            if resp.status_code == 200:
                expired = resp.json().get("expired", [])
                if expired:
                    logger.info(f"Закрито прострочених квестів: {expired}")
    except Exception as e:
        logger.error(f"Помилка expire-quests: {e}")
