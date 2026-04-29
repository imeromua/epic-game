from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from api.core.database import get_db
from api.core.security import get_current_player
from api.models.player import Player

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


@router.get("/me", response_model=PlayerProfile)
async def get_my_profile(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    player_id = int(current["sub"])
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(404, detail="Гравця не знайдено")

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
    )


@router.patch("/me")
async def update_my_profile(
    name: Optional[str] = None,
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    player_id = int(current["sub"])
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(404)

    if name:
        player.name = name.strip()[:128]

    return {"ok": True}
