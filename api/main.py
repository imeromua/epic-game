from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from api.core.config import settings
from api.core.database import init_db
from api.core.redis import init_redis, close_redis
from api.routers import auth, players, quests, prizes, admin, leaderboard


# Налаштування логування
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cтарт і зупинка застосунку"""
    logger.info("🚀 EpicTeam Drive API стартує...")
    await init_db()
    await init_redis()
    yield
    await close_redis()
    logger.info("🛑 API зупинено")


app = FastAPI(
    title="EpicTeam Drive API",
    description="Backend для корпоративної платформи гейміфікації",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# CORS — дозволяємо MiniApp обращатись до API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутери
app.include_router(auth.router,        prefix="/auth",        tags=["auth"])
app.include_router(players.router,     prefix="/players",     tags=["players"])
app.include_router(quests.router,      prefix="/quests",      tags=["quests"])
app.include_router(prizes.router,      prefix="/prizes",      tags=["prizes"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(admin.router,       prefix="/admin",       tags=["admin"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "EpicTeam Drive API"}
