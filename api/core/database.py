from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from api.core.config import settings
from loguru import logger


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI Dependency — сесія БД на один запит"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Cтворення таблиць (для дев режиму, в продукшн — alembic)"""
    async with engine.begin() as conn:
        from api.models import player, quest, prize, announcement  # noqa
        await conn.run_sync(Base.metadata.create_all)
        logger.info("БД ініціалізовано")
