import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
import pytz
import sys

from scheduler.config import sched_settings
from scheduler.jobs import (
    job_morning_digest,
    job_evening_summary,
    job_reset_daily_leaderboard,
    job_random_event_window,
    job_check_expired_quests,
)


async def main():
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:HH:mm:ss} | {level} | {message}",
        level="INFO",
        colorize=True,
    )

    tz = pytz.timezone(sched_settings.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # 09:00 — Ранковий дайджест і топ-5
    scheduler.add_job(
        job_morning_digest,
        CronTrigger(hour=9, minute=0, timezone=tz),
        id="morning_digest",
        replace_existing=True,
    )

    # 21:00 — Вечірній підсумок
    scheduler.add_job(
        job_evening_summary,
        CronTrigger(hour=21, minute=0, timezone=tz),
        id="evening_summary",
        replace_existing=True,
    )

    # 00:01 — Скидання денного лідерборду
    scheduler.add_job(
        job_reset_daily_leaderboard,
        CronTrigger(hour=0, minute=1, timezone=tz),
        id="reset_daily",
        replace_existing=True,
    )

    # 08:00–10:00 і 13:00–15:00 — Вікна рандомних івентів
    # Запускаємо перевірку кожні 10 хв — саме вікно вирішує, запускати чи ні
    scheduler.add_job(
        job_random_event_window,
        IntervalTrigger(minutes=10, timezone=tz),
        id="random_event",
        replace_existing=True,
    )

    # Кожну хвилину — закриваємо прострочені квести
    scheduler.add_job(
        job_check_expired_quests,
        IntervalTrigger(minutes=1),
        id="check_expired",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("⏰ Scheduler запущено")

    try:
        await asyncio.Event().wait()  # вічно чекаємо
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler зупинено")


if __name__ == "__main__":
    asyncio.run(main())
