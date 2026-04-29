from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import imagehash
from PIL import Image
import io

from api.core.database import get_db
from api.core.security import get_current_player
from api.core.redis import get_redis, RedisKeys
from api.models.quest import Quest, QuestStatus, QuestType
from api.models.player import Player
from api.services.quest_service import QuestService

router = APIRouter()


# ==========================================
# Схеми відповідей
# ==========================================

class QuestOut(BaseModel):
    id: int
    title: str
    description: str
    category: int
    quest_type: str
    time_limit_minutes: int
    xp_reward: int
    status: str
    started_at: Optional[datetime]
    prize_emoji: Optional[str]
    prize_name: Optional[str]

    class Config:
        from_attributes = True


class AnswerRequest(BaseModel):
    quest_id: int
    answer_text: Optional[str] = None


class AnswerResponse(BaseModel):
    status: str          # winner | loser | expired | pending_validation | duplicate_photo
    xp_earned: int = 0
    winner_name: Optional[str] = None
    message: str = ""


# ==========================================
# GET /quests/active — поточний активний квест
# ==========================================

@router.get("/active", response_model=Optional[QuestOut])
async def get_active_quest(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Quest)
        .where(Quest.status == QuestStatus.ACTIVE)
        .order_by(Quest.started_at.desc())
        .limit(1)
    )
    quest = result.scalar_one_or_none()
    if not quest:
        return None

    prize_emoji = None
    prize_name = None
    if quest.prize:
        prize_emoji = quest.prize.emoji
        prize_name = quest.prize.name

    return QuestOut(
        id=quest.id,
        title=quest.title,
        description=quest.description,
        category=quest.category.value,
        quest_type=quest.quest_type.value,
        time_limit_minutes=quest.time_limit_minutes,
        xp_reward=quest.xp_reward,
        status=quest.status.value,
        started_at=quest.started_at,
        prize_emoji=prize_emoji,
        prize_name=prize_name,
    )


# ==========================================
# GET /quests/history — останні 20 квестів гравця
# ==========================================

@router.get("/history")
async def quest_history(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    from api.models.quest import QuestResult
    from sqlalchemy.orm import selectinload

    player_id = int(current["sub"])
    result = await db.execute(
        select(QuestResult)
        .where(QuestResult.player_id == player_id)
        .order_by(QuestResult.submitted_at.desc())
        .limit(20)
        .options(selectinload(QuestResult.quest))
    )
    rows = result.scalars().all()

    return [
        {
            "quest_title": r.quest.title,
            "quest_category": r.quest.category.value,
            "is_winner": r.is_winner,
            "xp_earned": r.xp_earned,
            "submitted_at": r.submitted_at,
        }
        for r in rows
    ]


# ==========================================
# POST /quests/answer — текстова/вибір відповідь
# ==========================================

@router.post("/answer", response_model=AnswerResponse)
async def submit_text_answer(
    body: AnswerRequest,
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    player_id = int(current["sub"])

    # Завантажуємо квест
    result = await db.execute(select(Quest).where(Quest.id == body.quest_id))
    quest = result.scalar_one_or_none()
    if not quest or quest.status != QuestStatus.ACTIVE:
        raise HTTPException(404, detail="Квест не знайдено або не активний")

    if quest.quest_type == QuestType.PHOTO:
        raise HTTPException(400, detail="Цей квест потребує фото")

    # Завантажуємо гравця
    r = await db.execute(select(Player).where(Player.id == player_id))
    player = r.scalar_one_or_none()
    if not player:
        raise HTTPException(404, detail="Гравця не знайдено")

    result_data = await QuestService.submit_answer(
        db, quest, player, answer_text=body.answer_text
    )

    messages = {
        "winner": f"🏆 Вітаємо! Ви перший! +{result_data.get('xp_earned', 0)} XP",
        "loser": f"😔 {result_data.get('winner_name', 'Хтось')} виявився спритнішим! Наступного разу!",
        "expired": "⏰ Час вийшов!",
    }

    return AnswerResponse(
        status=result_data["status"],
        xp_earned=result_data.get("xp_earned", 0),
        winner_name=result_data.get("winner_name"),
        message=messages.get(result_data["status"], ""),
    )


# ==========================================
# POST /quests/photo — фото-відповідь
# ==========================================

@router.post("/photo", response_model=AnswerResponse)
async def submit_photo_answer(
    quest_id: int = Form(...),
    photo: UploadFile = File(...),
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    player_id = int(current["sub"])

    result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = result.scalar_one_or_none()
    if not quest or quest.status != QuestStatus.ACTIVE:
        raise HTTPException(404, detail="Квест не активний")

    r = await db.execute(select(Player).where(Player.id == player_id))
    player = r.scalar_one_or_none()

    # Обчислюємо pHash для анти-фрод перевірки
    photo_bytes = await photo.read()
    image = Image.open(io.BytesIO(photo_bytes))
    phash = str(imagehash.phash(image))

    result_data = await QuestService.submit_answer(
        db, quest, player,
        photo_file_id=photo.filename,  # реальний file_id прийде з бота
        photo_hash=phash,
    )

    messages = {
        "pending_validation": "📸 Фото прийнято! Очікуємо підтвердження від адміна...",
        "loser": f"😔 {result_data.get('winner_name', 'Хтось')} встиг першим!",
        "duplicate_photo": "⚠️ Це фото вже було надіслано!",
        "expired": "⏰ Час вийшов!",
    }

    return AnswerResponse(
        status=result_data["status"],
        winner_name=result_data.get("winner_name"),
        message=messages.get(result_data["status"], ""),
    )
