from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, date

from api.core.database import get_db
from api.models.quest import Quest, QuestStatus, QuestType, QuestCategory, QuestResult
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
    is_template: bool = False
    template_name: Optional[str] = None


class ValidatePhotoRequest(BaseModel):
    approved: bool


async def _get_admin(tg_id_str: str | None, db: AsyncSession) -> Player:
    if not tg_id_str:
        raise HTTPException(403, detail="Відсутній X-TG-ID")
    r = await db.execute(select(Player).where(
        Player.tg_id == int(tg_id_str),
        Player.is_admin == True,
    ))
    admin = r.scalar_one_or_none()
    if not admin:
        raise HTTPException(403, detail="Не адмін")
    return admin


# ==========================================
# POST /admin/quests
# ==========================================

@router.post("/quests")
async def create_quest(
    body: CreateQuestRequest,
    x_tg_id: Optional[str] = Header(None, alias="X-TG-ID"),
    db: AsyncSession = Depends(get_db),
):
    admin = await _get_admin(x_tg_id, db)

    quest = Quest(
        title=body.title,
        description=body.description,
        category=QuestCategory(body.category),
        quest_type=QuestType(body.quest_type),
        time_limit_minutes=body.time_limit_minutes,
        xp_reward=body.xp_reward,
        scheduled_at=body.scheduled_at,
        is_template=body.is_template,
        template_name=body.template_name,
        created_by=admin.id,
    )
    db.add(quest)
    await db.flush()

    if body.start_now:
        quest = await QuestService.start_quest(db, quest)

    return {
        "id": quest.id,
        "title": quest.title,
        "status": quest.status.value,
        "category": quest.category.value,
        "prize_name": quest.prize.name if quest.prize else None,
        "prize_emoji": quest.prize.emoji if quest.prize else None,
        "xp_reward": quest.xp_reward,
        "time_limit_minutes": quest.time_limit_minutes,
    }


# ==========================================
# GET /admin/quest-templates  — scheduler
# ==========================================

@router.get("/quest-templates")
async def get_quest_templates(db: AsyncSession = Depends(get_db)):
    """Scheduler використовує для рандомних івентів"""
    result = await db.execute(
        select(Quest).where(Quest.is_template == True)
    )
    templates = result.scalars().all()
    return [
        {
            "title": t.title,
            "description": t.description,
            "category": t.category.value,
            "quest_type": t.quest_type.value,
            "time_limit_minutes": t.time_limit_minutes,
            "xp_reward": t.xp_reward,
        }
        for t in templates
    ]


# ==========================================
# GET /admin/daily-quest-count  — scheduler
# ==========================================

@router.get("/daily-quest-count")
async def daily_quest_count(
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Kількість квестів за день (не шаблонів)"""
    from sqlalchemy import cast, Date as SADate
    target = date or datetime.now(timezone.utc).date().isoformat()

    result = await db.execute(
        select(func.count(Quest.id)).where(
            Quest.is_template == False,
            cast(Quest.created_at, SADate) == target,
        )
    )
    count = result.scalar_one_or_none() or 0
    return {"count": count, "date": target}


# ==========================================
# POST /admin/expire-quests  — scheduler
# ==========================================

@router.post("/expire-quests")
async def expire_quests(db: AsyncSession = Depends(get_db)):
    """Закриває всі прострочені ACTIVE квести"""
    from api.core.redis import get_redis, RedisKeys
    redis = get_redis()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Quest).where(Quest.status == QuestStatus.ACTIVE)
    )
    active_quests = result.scalars().all()

    expired_ids = []
    for quest in active_quests:
        key = RedisKeys.quest_status(quest.id)
        still_active = await redis.exists(key)
        if not still_active:
            quest.status = QuestStatus.EXPIRED
            quest.closed_at = now
            expired_ids.append(quest.id)

    if expired_ids:
        await db.commit()

    return {"expired": expired_ids}


# ==========================================
# GET /admin/pending-photos
# ==========================================

@router.get("/pending-photos")
async def get_pending_photos(
    x_tg_id: Optional[str] = Header(None, alias="X-TG-ID"),
    db: AsyncSession = Depends(get_db),
):
    await _get_admin(x_tg_id, db)
    from sqlalchemy.orm import selectinload

    rows_result = await db.execute(
        select(QuestResult)
        .where(
            QuestResult.is_winner == True,
            QuestResult.photo_validated.is_(None),
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
    admin = await _get_admin(x_tg_id, db)

    r = await db.execute(select(QuestResult).where(QuestResult.id == result_id))
    result = r.scalar_one_or_none()
    if not result:
        raise HTTPException(404)

    result.photo_validated = body.approved
    result.validated_by = admin.id
    result.validated_at = datetime.now(timezone.utc)

    if body.approved:
        pr = await db.execute(select(Player).where(Player.id == result.player_id))
        player = pr.scalar_one()
        qr = await db.execute(select(Quest).where(Quest.id == result.quest_id))
        quest = qr.scalar_one()

        from api.services.quest_service import XP_BY_CATEGORY
        xp = XP_BY_CATEGORY[quest.category]
        result.xp_earned = xp
        await QuestService._award_player(db, player, quest, xp, None)
        quest.status = QuestStatus.CLOSED
        quest.closed_at = datetime.now(timezone.utc)

    return {"ok": True, "approved": body.approved}


# ==========================================
# GET /admin/stats  — адмін панель
# ==========================================

@router.get("/stats")
async def admin_stats(
    x_tg_id: Optional[str] = Header(None, alias="X-TG-ID"),
    db: AsyncSession = Depends(get_db),
):
    await _get_admin(x_tg_id, db)

    total_quests = (await db.execute(
        select(func.count(Quest.id)).where(Quest.is_template == False)
    )).scalar_one_or_none() or 0

    total_players = (await db.execute(
        select(func.count(Player.id)).where(Player.is_active == True)
    )).scalar_one_or_none() or 0

    # Найчастіші шаблони (хітмап слабких місць залу)
    from sqlalchemy import desc
    popular = (await db.execute(
        select(Quest.template_name, func.count(Quest.id).label("cnt"))
        .where(
            Quest.is_template == False,
            Quest.template_name.isnot(None),
        )
        .group_by(Quest.template_name)
        .order_by(desc("cnt"))
        .limit(5)
    )).all()

    return {
        "total_quests": total_quests,
        "total_players": total_players,
        "popular_templates": [
            {"template": row[0], "count": row[1]} for row in popular
        ],
    }
