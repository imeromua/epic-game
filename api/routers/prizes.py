from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from api.core.database import get_db
from api.core.security import get_current_player
from api.models.prize import Prize, PrizeTransaction
from api.models.player import Player

router = APIRouter()


class PrizeOut(BaseModel):
    id: int
    name: str
    emoji: str
    category: int
    cost_uah: int
    xp_cost: int
    is_rare: bool
    stock: Optional[int]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[PrizeOut])
async def list_prizes(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Магазин призів — для MiniApp"""
    result = await db.execute(
        select(Prize)
        .where(Prize.is_active == True)
        .order_by(Prize.category, Prize.weight.desc())
    )
    prizes = result.scalars().all()

    return [
        PrizeOut(
            id=p.id,
            name=p.name,
            emoji=p.emoji,
            category=p.category.value,
            cost_uah=p.cost_uah,
            xp_cost=p.xp_cost,
            is_rare=p.is_rare,
            stock=p.stock,
        )
        for p in prizes
    ]


@router.get("/my-prizes")
async def my_prize_history(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Історія виграних призів — MiniApp ‘Історія успіху’"""
    player_id = int(current["sub"])
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(PrizeTransaction)
        .where(PrizeTransaction.player_id == player_id)
        .order_by(PrizeTransaction.created_at.desc())
        .limit(50)
        .options(selectinload(PrizeTransaction.prize))
    )
    rows = result.scalars().all()

    return [
        {
            "prize_name": r.prize.name,
            "prize_emoji": r.prize.emoji,
            "is_issued": r.is_issued,
            "source": r.source,
            "created_at": r.created_at,
        }
        for r in rows
    ]
