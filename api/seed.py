"""
Seed-скрипт: заповнює БД стартовими призами та шаблонами квестів.
Запуск: python -m api.seed
"""
import asyncio
from loguru import logger
from api.core.database import init_db, AsyncSessionLocal
from api.models.prize import Prize, PrizeCategory, PrizeType
from api.models.quest import Quest, QuestCategory, QuestType, QuestStatus
from sqlalchemy import select


PRIZES = [
    # ===================== ⭐ EASY (1) =====================
    dict(
        name="Кава / лате",
        emoji="☕",
        category=PrizeCategory.EASY,
        prize_type=PrizeType.MATERIAL,
        cost_uah=55,
        weight=40,
    ),
    dict(
        name="Шоколадний батончик",
        emoji="🍫",
        category=PrizeCategory.EASY,
        prize_type=PrizeType.MATERIAL,
        cost_uah=30,
        weight=35,
    ),
    dict(
        name="+15 хв до перерви",
        emoji="⏰",
        category=PrizeCategory.EASY,
        prize_type=PrizeType.NON_MATERIAL,
        cost_uah=0,
        weight=25,
    ),
    # ===================== ⭐⭐ MEDIUM (2) =====================
    dict(
        name="Бургер в кафетерії",
        emoji="🍔",
        category=PrizeCategory.MEDIUM,
        prize_type=PrizeType.MATERIAL,
        cost_uah=120,
        weight=35,
    ),
    dict(
        name="Сет снеків до кави",
        emoji="🍩",
        category=PrizeCategory.MEDIUM,
        prize_type=PrizeType.MATERIAL,
        cost_uah=80,
        weight=30,
    ),
    dict(
        name="Вибір зміни (1 раз на місяць)",
        emoji="🗓️",
        category=PrizeCategory.MEDIUM,
        prize_type=PrizeType.NON_MATERIAL,
        cost_uah=0,
        weight=20,
    ),
    dict(
        name="Піца / суші на обід",
        emoji="🍕",
        category=PrizeCategory.MEDIUM,
        prize_type=PrizeType.MATERIAL,
        cost_uah=150,
        weight=15,
    ),
    # ===================== ⭐⭐⭐ HARD (3) =====================
    dict(
        name="Подарункова картка 300 ₴",
        emoji="💳",
        category=PrizeCategory.HARD,
        prize_type=PrizeType.MATERIAL,
        cost_uah=300,
        weight=30,
        is_rare=True,
    ),
    dict(
        name="Додатковий вихідний день",
        emoji="🏖️",
        category=PrizeCategory.HARD,
        prize_type=PrizeType.NON_MATERIAL,
        cost_uah=0,
        weight=20,
        stock_monthly_limit=1,
    ),
    # ===================== 💎 LEGENDARY (4) =====================
    dict(
        name="Бонус 1000 ₴",
        emoji="💰",
        category=PrizeCategory.LEGENDARY,
        prize_type=PrizeType.MATERIAL,
        cost_uah=1000,
        weight=10,
        is_rare=True,
        stock_monthly_limit=1,
    ),
]


QUEST_TEMPLATES = [
    dict(
        title="🔍 Шукач свіжості",
        description=(
            "Хто перший знайде товар з терміном придатності, "
            "що минає через 2 дні? — зроби фото товару + цінник!"
        ),
        category=QuestCategory.EASY,
        quest_type=QuestType.PHOTO,
        time_limit_minutes=5,
        xp_reward=50,
        is_template=True,
        template_name="expiry_hunt",
    ),
    dict(
        title="📌 Де стоїть ламінат??",
        description=(
            "Озведеть, в якому секторі торгового залу "
            "презентовано ламінат серії \u00abClic\u00bb?"
        ),
        category=QuestCategory.MEDIUM,
        quest_type=QuestType.TEXT,
        time_limit_minutes=3,
        xp_reward=120,
        is_template=True,
        template_name="location_quiz",
    ),
    dict(
        title="❓ Ціна дня",
        description=(
            "Яка поточна ціна на плитку кераміку моделі КерамГраніт 600\u04452 "
            "беж-білий?"
        ),
        category=QuestCategory.MEDIUM,
        quest_type=QuestType.TEXT,
        time_limit_minutes=2,
        xp_reward=120,
        is_template=True,
        template_name="price_quiz",
    ),
    dict(
        title="📸 Секція викладки",
        description=(
            "Знайди товар з цінником, що виступає з полиця, "
            "і зроби фото розкладки + осьередку."
        ),
        category=QuestCategory.EASY,
        quest_type=QuestType.PHOTO,
        time_limit_minutes=5,
        xp_reward=50,
        is_template=True,
        template_name="display_check",
    ),
    dict(
        title="💎 Легендарний обхід!!",
        description=(
            "Хто перший знайде і сфотографує всі 5 очок відділу сантехніки "
            "з розподілом цін: повінні бути видні цінники!"
        ),
        category=QuestCategory.LEGENDARY,
        quest_type=QuestType.PHOTO,
        time_limit_minutes=10,
        xp_reward=1000,
        is_template=True,
        template_name="legendary_tour",
    ),
]


async def run_seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Призи
        existing = await session.execute(select(Prize).limit(1))
        if not existing.scalar_one_or_none():
            for p in PRIZES:
                session.add(Prize(**p))
            logger.info(f"Додано {len(PRIZES)} призів")
        else:
            logger.info("Призи вже існують, пропускаємо")

        # Шаблони квестів
        existing_q = await session.execute(
            select(Quest).where(Quest.is_template == True).limit(1)
        )
        if not existing_q.scalar_one_or_none():
            for q in QUEST_TEMPLATES:
                session.add(Quest(
                    **q,
                    status=QuestStatus.PENDING,
                    xp_participation=10,
                ))
            logger.info(f"Додано {len(QUEST_TEMPLATES)} шаблонів квестів")
        else:
            logger.info("Шаблони вже існують, пропускаємо")

        await session.commit()
        logger.info("✅ Seed завершено")


if __name__ == "__main__":
    asyncio.run(run_seed())
