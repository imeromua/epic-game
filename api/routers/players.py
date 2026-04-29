from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from api.core.database import get_db
from api.core.security import get_current_player
from api.models.player import Player
from api.models.quest import QuestResult, Quest
from api.models.prize import PrizeTransaction, Prize

router = APIRouter()


class PlayerProfile(BaseModel):
    id: int
    name: str
    tg_username: Optional[str]
    xp: int
    rank: str
    rank_display: str
    streak: int
    quests_won: int
    legendary_wins: int
    is_admin: bool


class HistoryItem(BaseModel):
    type: str              # 'quest' | 'prize'
    title: str
    subtitle: Optional[str]
    is_winner: Optional[bool]
    xp_earned: int
    emoji: Optional[str]
    date: datetime


# ===================================================
# GET /players/me
# ===================================================

@router.get("/me", response_model=PlayerProfile)
async def get_my_profile(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    player = await _get_player(int(current["sub"]), db)
    return _to_profile(player)


# ===================================================
# GET /players/me/history
# ===================================================

@router.get("/me/history")
async def get_my_history(
    limit: int = 30,
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    player_id = int(current["sub"])

    # Quest results
    qr_result = await db.execute(
        select(QuestResult)
        .where(QuestResult.player_id == player_id)
        .options(selectinload(QuestResult.quest))
        .order_by(QuestResult.submitted_at.desc())
        .limit(limit)
    )
    quest_results = qr_result.scalars().all()

    # Prize transactions
    pt_result = await db.execute(
        select(PrizeTransaction)
        .where(PrizeTransaction.player_id == player_id)
        .options(selectinload(PrizeTransaction.prize))
        .order_by(PrizeTransaction.created_at.desc())
        .limit(limit)
    )
    prize_txs = pt_result.scalars().all()

    # Merge + sort by date
    items = []

    for qr in quest_results:
        items.append(HistoryItem(
            type="quest",
            title=qr.quest.title if qr.quest else "Квест",
            subtitle="Переможець! 🏆" if qr.is_winner else "Учасник",
            is_winner=qr.is_winner,
            xp_earned=qr.xp_earned,
            emoji="⚡" if qr.is_winner else "👀",
            date=qr.submitted_at,
        ))

    for tx in prize_txs:
        items.append(HistoryItem(
            type="prize",
            title=tx.prize.name if tx.prize else "Приз",
            subtitle="Видано" if tx.is_issued else "Очікує видачі",
            is_winner=None,
            xp_earned=0,
            emoji=tx.prize.emoji if tx.prize else "🎁",
            date=tx.created_at,
        ))

    items.sort(key=lambda x: x.date, reverse=True)

    return {"history": [i.model_dump() for i in items[:limit]]}


# ===================================================
# GET /players/by-tg/{tg_id}  (internal, bot)
# ===================================================

@router.get("/by-tg/{tg_id}", response_model=PlayerProfile)
async def get_player_by_tg(
    tg_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Player).where(Player.tg_id == tg_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(404, detail="Гравця не знайдено")
    return _to_profile(player)


# ===================================================
# PATCH /players/me
# ===================================================

@router.patch("/me")
async def update_my_profile(
    name: Optional[str] = None,
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    player = await _get_player(int(current["sub"]), db)
    if name:
        player.name = name.strip()[:128]
    await db.commit()
    return {"ok": True}


# ===================================================
# Helpers
# ===================================================

async def _get_player(player_id: int, db: AsyncSession) -> Player:
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(404, detail="Гравця не знайдено")
    return player


def _to_profile(player: Player) -> PlayerProfile:
    return PlayerProfile(
        id=player.id,
        name=player.name,
        tg_username=player.tg_username,
        xp=player.xp,
        rank=player.rank.value,
        rank_display=player.rank_display,
        streak=player.streak,
        quests_won=player.quests_won,
        legendary_wins=player.legendary_wins,
        is_admin=player.is_admin,
    )
