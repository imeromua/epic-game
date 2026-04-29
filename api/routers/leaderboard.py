from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from api.core.database import get_db
from api.core.security import get_current_player
from api.core.redis import get_redis, RedisKeys
from api.models.player import Player

router = APIRouter()


class LeaderboardEntry(BaseModel):
    rank: int
    player_id: int
    name: str
    tg_username: str | None
    xp: int
    rank_title: str
    streak: int
    quests_won: int
    is_me: bool


@router.get("/monthly", response_model=List[LeaderboardEntry])
async def monthly_leaderboard(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """
    ТОП-12 за місяць з Redis Sorted Set.
    Оновлюється в реальному часі після кожної перемоги.
    """
    redis = get_redis()
    my_id = int(current["sub"])

    # ZREVRANGE — від найбільшого XP до найменшого, з балами
    entries = await redis.zrevrange(
        RedisKeys.leaderboard_monthly(), 0, 11, withscores=True
    )

    if not entries:
        return []

    player_ids = [int(pid) for pid, _ in entries]
    result = await db.execute(
        select(Player).where(Player.id.in_(player_ids))
    )
    players_map = {p.id: p for p in result.scalars().all()}

    board = []
    for pos, (pid_str, score) in enumerate(entries, start=1):
        pid = int(pid_str)
        p = players_map.get(pid)
        if not p:
            continue
        board.append(LeaderboardEntry(
            rank=pos,
            player_id=p.id,
            name=p.name,
            tg_username=p.tg_username,
            xp=int(score),
            rank_title=p.rank_display,
            streak=p.streak,
            quests_won=p.quests_won,
            is_me=(pid == my_id),
        ))

    return board


@router.get("/daily", response_model=List[LeaderboardEntry])
async def daily_leaderboard(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """ТОП-5 за сьогодні — для ранкового дайджесту бота"""
    redis = get_redis()
    my_id = int(current["sub"])

    entries = await redis.zrevrange(
        RedisKeys.leaderboard_daily(), 0, 4, withscores=True
    )
    if not entries:
        return []

    player_ids = [int(pid) for pid, _ in entries]
    result = await db.execute(
        select(Player).where(Player.id.in_(player_ids))
    )
    players_map = {p.id: p for p in result.scalars().all()}

    return [
        LeaderboardEntry(
            rank=pos,
            player_id=p.id if (p := players_map.get(int(pid_str))) else 0,
            name=p.name if p else "?",
            tg_username=p.tg_username if p else None,
            xp=int(score),
            rank_title=p.rank_display if p else "",
            streak=p.streak if p else 0,
            quests_won=p.quests_won if p else 0,
            is_me=(int(pid_str) == my_id),
        )
        for pos, (pid_str, score) in enumerate(entries, start=1)
        if (p := players_map.get(int(pid_str)))
    ]


@router.get("/my-stats")
async def my_stats(
    current: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Статистика поточного гравця для Dashboard MiniApp"""
    redis = get_redis()
    player_id = int(current["sub"])

    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        return {}

    # Позиція в місячному рейтингу
    monthly_rank = await redis.zrevrank(
        RedisKeys.leaderboard_monthly(), str(player_id)
    )

    # Cooldown — скільки секунд до наступної можливої перемоги
    cooldown_ttl = await redis.ttl(RedisKeys.player_cooldown(player_id))

    return {
        "player_id": player.id,
        "name": player.name,
        "xp": player.xp,
        "xp_total": player.xp_total,
        "rank": player.rank.value,
        "rank_display": player.rank_display,
        "streak": player.streak,
        "streak_max": player.streak_max,
        "quests_won": player.quests_won,
        "quests_participated": player.quests_participated,
        "legendary_wins": player.legendary_wins,
        "monthly_position": (monthly_rank + 1) if monthly_rank is not None else None,
        "cooldown_seconds": max(0, cooldown_ttl),
        "is_on_cooldown": cooldown_ttl > 0,
    }
