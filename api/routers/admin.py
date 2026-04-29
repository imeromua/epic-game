from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from api.core.database import get_db
from api.core.security import require_admin, get_current_player
from api.models.quest import Quest, QuestStatus, QuestType, QuestCategory
from api.models.quest import QuestResult
from api.models.player import Player
from api.services.quest_service import QuestService

router = APIRouter()


class CreateQuestRequest(BaseModel):
    title: str
    description: str
    category: int
    quest_type: str
    time_limit_minutes: int = 5
    xp_reward: int
    start_now: bool = False
    scheduled_at: Optional[datetime] = None


class ValidatePhotoRequest(BaseModel):
    approved: bool


# ==========================================
# POST /admin/quests — створення квесту
# ==========================================

@router.post("/quests")
async def create_quest(
    body: CreateQuestRequest,
    x_tg_id: Optional[str] = Header(None, alias="X-TG-ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Створення квесту. Аутентифікація через X-TG-ID з бота
    або Authorization JWT з MiniApp.
    """
    # Перевірка адміна
    if x_tg_id:
        r = await db.execute(select(Player).where(
            Player.tg_id == int(x_tg_id),
            Player.is_admin == True,
        ))
        if not r.scalar_one_or_none():
            raise HTTPException(403, detail="Не адмін")

    quest = Quest(
        title=body.title,
        description=body.description,
        category=QuestCategory(body.category),
        quest_type=QuestType(body.quest_type),
        time_limit_minutes=body.time_limit_minutes,
        xp_reward=body.xp_reward,
        scheduled_at=body.scheduled_at,
    )
    db.add(quest)
    await db.flush()

    if body.start_now:
        quest = await QuestService.start_quest(db, quest)

    return {
        "id": quest.id,
        "title": quest.title,
        "status": quest.status.value,
        "prize_name": quest.prize.name if quest.prize else None,
    }


# ==========================================
# GET /admin/pending-photos
# ==========================================

@router.get("/pending-photos")
async def get_pending_photos(
    x_tg_id: Optional[str] = Header(None, alias="X-TG-ID"),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload

    rows_result = await db.execute(
        select(QuestResult)
        .where(
            QuestResult.is_winner == True,
            QuestResult.photo_validated == None,
        )
        .options(
            selectinload(QuestResult.player),
            selectinload(QuestResult.quest),
        )
        .order_by(QuestResult.submitted_at)
        .limit(20)
    )
    rows = rows_result.scalars().all()

    return [
        {
            "result_id": r.id,
            "player_name": r.player.name,
            "photo_file_id": r.photo_file_id,
            "quest_title": r.quest.title,
            "submitted_at": r.submitted_at,
        }
        for r in rows
    ]


# ==========================================
# POST /admin/validate-photo/{result_id}
# ==========================================

@router.post("/validate-photo/{result_id}")
async def validate_photo(
    result_id: int,
    body: ValidatePhotoRequest,
    x_tg_id: Optional[str] = Header(None, alias="X-TG-ID"),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(QuestResult).where(QuestResult.id == result_id))
    result = r.scalar_one_or_none()
    if not result:
        raise HTTPException(404)

    # Завантажуємо адміна
    admin_result = await db.execute(select(Player).where(
        Player.tg_id == int(x_tg_id or 0),
        Player.is_admin == True,
    ))
    admin = admin_result.scalar_one_or_none()
    if not admin:
        raise HTTPException(403)

    result.photo_validated = body.approved
    result.validated_by = admin.id
    result.validated_at = datetime.now(timezone.utc)

    if body.approved:
        # Нараховуємо XP
        player_r = await db.execute(select(Player).where(Player.id == result.player_id))
        player = player_r.scalar_one()
        quest_r = await db.execute(select(Quest).where(Quest.id == result.quest_id))
        quest = quest_r.scalar_one()

        from api.services.quest_service import XP_BY_CATEGORY
        xp = XP_BY_CATEGORY[quest.category]
        result.xp_earned = xp

        await QuestService._award_player(db, player, quest, xp, None)

        # Закриваємо квест
        quest.status = QuestStatus.CLOSED
        quest.closed_at = datetime.now(timezone.utc)

    return {"ok": True, "approved": body.approved}
