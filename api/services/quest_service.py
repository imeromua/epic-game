import random
import asyncio
from datetime import datetime, timezone
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.core.redis import get_redis, RedisKeys
from api.models.quest import Quest, QuestResult, QuestStatus, QuestCategory
from api.models.prize import Prize, PrizeCategory
from api.models.player import Player


# ==========================================
# XP нарахування за категорією
# ==========================================
XP_BY_CATEGORY = {
    QuestCategory.EASY: 50,
    QuestCategory.MEDIUM: 120,
    QuestCategory.HARD: 250,
    QuestCategory.LEGENDARY: 1000,
}

XP_PARTICIPATION = 10      # за участь (не перемога)
XP_FIRST_WIN_DAY = 20      # перша перемога дня
XP_SPEED_RECORD = 30       # рекорд швидкості дня
COOLDOWN_SECONDS = 7200    # 2 годи після перемоги


class QuestService:

    # ==========================================
    # Вибір призу (Weighted Random)
    # ==========================================

    @staticmethod
    async def pick_random_prize(db: AsyncSession, category: QuestCategory) -> Prize | None:
        """
        Зважена рандомізація — приз з вагою 40 випадає
        вчетверо частіше ніж приз з вагою 10.
        """
        prize_category = PrizeCategory(category.value)

        result = await db.execute(
            select(Prize).where(
                Prize.category == prize_category,
                Prize.is_active == True,
                # Сток: None = безлімітний, > 0 = є залишок
                (Prize.stock == None) | (Prize.stock > 0),
            )
        )
        prizes = result.scalars().all()

        if not prizes:
            logger.warning(f"Немає доступних призів категорії {prize_category}")
            return None

        total_weight = sum(p.weight for p in prizes)
        rand = random.uniform(0, total_weight)
        cumulative = 0
        for prize in prizes:
            cumulative += prize.weight
            if rand <= cumulative:
                return prize

        return prizes[-1]  # fallback

    # ==========================================
    # Старт квесту
    # ==========================================

    @staticmethod
    async def start_quest(db: AsyncSession, quest: Quest) -> Quest:
        """Vідкриває вікно прийому відповідей"""
        redis = get_redis()
        ttl = quest.time_limit_minutes * 60

        # 1. Визначаємо приз
        prize = await QuestService.pick_random_prize(db, quest.category)
        if prize:
            quest.prize_id = prize.id

        # 2. Оновлюємо статус в БД
        quest.status = QuestStatus.ACTIVE
        quest.started_at = datetime.now(timezone.utc)

        # 3. Записуємо в Redis
        await redis.set(RedisKeys.quest_status(quest.id), "active", ex=ttl)
        await redis.set(RedisKeys.quest_winner(quest.id), "", ex=ttl)  # порожній

        logger.info(f"Квест #{quest.id} ({quest.category.name}) стартовано")
        return quest

    # ==========================================
    # First-Win — атомарна операція
    # ==========================================

    @staticmethod
    async def try_claim_winner(
        quest_id: int,
        player_id: int,
        ttl: int = 3600,
    ) -> bool:
        """
        Спроба зайняти позицію переможця.
        Redis SET NX — атомарна: лише перший SET True повертає True.
        """
        redis = get_redis()
        key = RedisKeys.quest_winner(quest_id)

        # nx=True — запише ТІЛЬКИ якщо ключ порожній
        result = await redis.set(key, str(player_id), nx=True, ex=ttl)
        return result is True

    # ==========================================
    # Обробка відповіді гравця
    # ==========================================

    @staticmethod
    async def submit_answer(
        db: AsyncSession,
        quest: Quest,
        player: Player,
        answer_text: str | None = None,
        photo_file_id: str | None = None,
        photo_hash: str | None = None,
    ) -> dict:
        """
        Повертає dict:
          {"status": "winner"} — цей гравець переміг
          {"status": "loser", "winner_name": str} — вже є переможець
          {"status": "expired"} — час вийшов
          {"status": "pending_validation"} — фото-квест, чекає адміна
        """
        redis = get_redis()

        # Перевірка: квест досі активний?
        status_key = await redis.get(RedisKeys.quest_status(quest.id))
        if not status_key:
            return {"status": "expired"}

        # Перевірка: дублікат фото
        if photo_hash:
            dup_key = f"quest:{quest.id}:photo_hashes"
            if await redis.sismember(dup_key, photo_hash):
                return {"status": "duplicate_photo"}
            await redis.sadd(dup_key, photo_hash)

        # Вимірюємо час відповіді
        time_to_win = datetime.now(timezone.utc) - quest.started_at.replace(tzinfo=timezone.utc)

        # Фото-квест: First-Win + пендінг валідації
        if quest.quest_type.value == "photo":
            is_winner = await QuestService.try_claim_winner(
                quest.id, player.id, quest.time_limit_minutes * 60
            )
            result_record = QuestResult(
                quest_id=quest.id,
                player_id=player.id,
                is_winner=is_winner,
                photo_file_id=photo_file_id,
                photo_hash=photo_hash,
                time_to_win=time_to_win,
                photo_validated=None,  # None = чекає адміна
            )
            db.add(result_record)

            if is_winner:
                return {"status": "pending_validation", "result_id": result_record.id}
            else:
                # Хто переміг?
                winner_id = await redis.get(RedisKeys.quest_winner(quest.id))
                winner = None
                if winner_id:
                    r = await db.execute(select(Player).where(Player.id == int(winner_id)))
                    winner = r.scalar_one_or_none()
                return {
                    "status": "loser",
                    "winner_name": winner.name if winner else "Хтось",
                }

        # Текст/вибір: First-Win атомарно
        is_winner = await QuestService.try_claim_winner(
            quest.id, player.id, quest.time_limit_minutes * 60
        )

        if is_winner:
            xp_earned = XP_BY_CATEGORY[quest.category]
            await QuestService._award_player(db, player, quest, xp_earned, time_to_win)
            return {"status": "winner", "xp_earned": xp_earned}
        else:
            # +XP за участь
            r = await db.execute(select(Player).where(Player.id == int(
                await redis.get(RedisKeys.quest_winner(quest.id)) or "0"
            )))
            winner = r.scalar_one_or_none()
            return {
                "status": "loser",
                "winner_name": winner.name if winner else "Хтось",
            }

    # ==========================================
    # Нарахування XP та оновлення рейтингу
    # ==========================================

    @staticmethod
    async def _award_player(
        db: AsyncSession,
        player: Player,
        quest: Quest,
        xp: int,
        time_to_win,
    ):
        redis = get_redis()

        # XP
        player.xp += xp
        player.xp_total += xp
        player.quests_won += 1
        player.rank = player.recalculate_rank()

        if quest.category.value == 4:  # LEGENDARY
            player.legendary_wins += 1
            player.rank = "legend"  # type: ignore

        # Оновлюємо leaderboard в Redis
        await redis.zadd(
            RedisKeys.leaderboard_monthly(),
            {str(player.id): player.xp},
        )
        await redis.zadd(
            RedisKeys.leaderboard_daily(),
            {str(player.id): player.xp},
        )

        # Cooldown
        await redis.set(
            RedisKeys.player_cooldown(player.id),
            "1",
            ex=COOLDOWN_SECONDS,
        )

        logger.info(f"Гравець #{player.id} отримав +{xp} XP (квест #{quest.id})")
