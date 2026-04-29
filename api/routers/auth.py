from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from loguru import logger

from api.core.database import get_db
from api.core.security import validate_telegram_init_data, create_access_token
from api.models.player import Player, PlayerRank
from api.core.redis import get_redis, RedisKeys

router = APIRouter()


class InitDataRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    player_id: int
    name: str
    xp: int
    rank: str
    is_new: bool  # чи новий гравець


@router.post("/signin", response_model=AuthResponse)
async def signin(
    body: InitDataRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Авторизація MiniApp.
    MiniApp надсилає Telegram.WebApp.initData —
    ми верифікуємо підпис і видаємо JWT.
    """
    # 1. Валідація підпису Telegram
    tg_user = validate_telegram_init_data(body.init_data)
    tg_id = tg_user.get("id")
    if not tg_id:
        raise HTTPException(status_code=400, detail="Відсутній user.id")

    # 2. Шукаємо або створюємо гравця
    result = await db.execute(select(Player).where(Player.tg_id == tg_id))
    player = result.scalar_one_or_none()
    is_new = False

    if not player:
        # Новий гравець — реєструємо
        first_name = tg_user.get("first_name", "")
        last_name = tg_user.get("last_name", "")
        username = tg_user.get("username")
        full_name = f"{first_name} {last_name}".strip() or username or str(tg_id)

        player = Player(
            tg_id=tg_id,
            tg_username=username,
            name=full_name,
        )
        db.add(player)
        await db.flush()  # доталкуємось id
        is_new = True
        logger.info(f"Новий гравець: {full_name} (tg_id={tg_id})")
    else:
        if not player.is_active:
            raise HTTPException(status_code=403, detail="Акаунт заблоковано")

    # 3. Оновлюємо leaderboard в Redis
    redis = get_redis()
    await redis.zadd(
        RedisKeys.leaderboard_monthly(),
        {str(player.id): player.xp},
        nx=True,  # не перезаписуємо якщо вже є
    )

    # 4. Видаємо JWT
    role = "admin" if player.is_admin else "player"
    token = create_access_token(player.id, tg_id, role)

    return AuthResponse(
        access_token=token,
        role=role,
        player_id=player.id,
        name=player.name,
        xp=player.xp,
        rank=player.rank_display,
        is_new=is_new,
    )
