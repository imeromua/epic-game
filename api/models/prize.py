from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from api.core.database import Base
import enum

if TYPE_CHECKING:
    from api.models.player import Player


class PrizeCategory(int, enum.Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    LEGENDARY = 4


class PrizeType(str, enum.Enum):
    MATERIAL = "material"
    NON_MATERIAL = "non_material"
    XP_SHOP = "xp_shop"


class Prize(Base):
    __tablename__ = "prizes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    emoji: Mapped[str] = mapped_column(String(8), default="🎁")

    category: Mapped[PrizeCategory] = mapped_column(
        SAEnum(PrizeCategory, values_callable=lambda x: [str(e.value) for e in x]),
        nullable=False,
    )
    prize_type: Mapped[PrizeType] = mapped_column(SAEnum(PrizeType), default=PrizeType.MATERIAL)

    weight: Mapped[int] = mapped_column(Integer, default=30)
    cost_uah: Mapped[int] = mapped_column(Integer, default=0)
    xp_cost: Mapped[int] = mapped_column(Integer, default=0)

    stock: Mapped[int | None] = mapped_column(Integer)
    stock_monthly_limit: Mapped[int | None] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_rare: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transactions: Mapped[list[PrizeTransaction]] = relationship(
        "PrizeTransaction", back_populates="prize"
    )


class PrizeTransaction(Base):
    __tablename__ = "prize_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)
    prize_id: Mapped[int] = mapped_column(Integer, ForeignKey("prizes.id"), nullable=False)
    quest_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("quests.id"))

    qr_token: Mapped[str] = mapped_column(String(64), unique=True)
    qr_expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    is_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    issued_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"))
    issued_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    source: Mapped[str] = mapped_column(String(32), default="quest")

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    player: Mapped[Player] = relationship(
        "Player",
        back_populates="prize_transactions",
        foreign_keys=[player_id],
    )
    prize: Mapped[Prize] = relationship("Prize", back_populates="transactions")
