from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import (
    BigInteger, Integer, String, Text, Interval,
    Enum as SAEnum, DateTime, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from api.core.database import Base
import enum

if TYPE_CHECKING:
    from api.models.player import Player
    from api.models.prize import Prize


class QuestCategory(int, enum.Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    LEGENDARY = 4


class QuestType(str, enum.Enum):
    PHOTO = "photo"
    TEXT = "text"
    CHOICE = "choice"


class QuestStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[QuestCategory] = mapped_column(
        SAEnum(QuestCategory, values_callable=lambda x: [str(e.value) for e in x]),
        nullable=False,
    )
    quest_type: Mapped[QuestType] = mapped_column(SAEnum(QuestType), nullable=False)

    correct_answer: Mapped[str | None] = mapped_column(Text)
    answer_options: Mapped[str | None] = mapped_column(Text)

    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=5)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_participation: Mapped[int] = mapped_column(Integer, default=10)

    prize_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("prizes.id"))
    prize: Mapped[Prize | None] = relationship("Prize")

    status: Mapped[QuestStatus] = mapped_column(
        SAEnum(QuestStatus), default=QuestStatus.PENDING
    )
    scheduled_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    tg_message_id: Mapped[int | None] = mapped_column(BigInteger)

    announce_30min: Mapped[bool] = mapped_column(default=False)
    announce_5min: Mapped[bool] = mapped_column(default=False)
    announce_text_30: Mapped[str | None] = mapped_column(Text)
    announce_text_5: Mapped[str | None] = mapped_column(Text)

    is_template: Mapped[bool] = mapped_column(default=False)
    template_name: Mapped[str | None] = mapped_column(String(128))

    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    results: Mapped[list[QuestResult]] = relationship(
        "QuestResult", back_populates="quest"
    )


class QuestResult(Base):
    __tablename__ = "quest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_id: Mapped[int] = mapped_column(Integer, ForeignKey("quests.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)

    is_winner: Mapped[bool] = mapped_column(default=False)
    answer_text: Mapped[str | None] = mapped_column(Text)
    photo_file_id: Mapped[str | None] = mapped_column(String(256))
    photo_hash: Mapped[str | None] = mapped_column(String(64))
    time_to_win: Mapped[Interval | None] = mapped_column(Interval)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)

    photo_validated: Mapped[bool | None] = mapped_column()
    validated_by: Mapped[int | None] = mapped_column(Integer)
    validated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    submitted_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    quest: Mapped[Quest] = relationship("Quest", back_populates="results")
    player: Mapped[Player] = relationship("Player", back_populates="quest_results")
