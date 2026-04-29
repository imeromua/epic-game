from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from api.core.database import Base
import enum

if TYPE_CHECKING:
    from api.models.quest import QuestResult
    from api.models.prize import PrizeTransaction


class PlayerRank(str, enum.Enum):
    NEWBIE = "newbie"
    SCOUT = "scout"
    EXPERT = "expert"
    MASTER = "master"
    LEGEND = "legend"


XP_RANK_THRESHOLDS = {
    PlayerRank.NEWBIE: 0,
    PlayerRank.SCOUT: 101,
    PlayerRank.EXPERT: 301,
    PlayerRank.MASTER: 601,
}


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))

    xp: Mapped[int] = mapped_column(Integer, default=0)
    xp_total: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[PlayerRank] = mapped_column(SAEnum(PlayerRank), default=PlayerRank.NEWBIE)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    streak_max: Mapped[int] = mapped_column(Integer, default=0)

    quests_won: Mapped[int] = mapped_column(Integer, default=0)
    quests_participated: Mapped[int] = mapped_column(Integer, default=0)
    legendary_wins: Mapped[int] = mapped_column(Integer, default=0)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    last_active_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    quest_results: Mapped[list[QuestResult]] = relationship(
        "QuestResult", back_populates="player"
    )
    prize_transactions: Mapped[list[PrizeTransaction]] = relationship(
        "PrizeTransaction",
        back_populates="player",
        foreign_keys="PrizeTransaction.player_id",
    )

    def recalculate_rank(self) -> PlayerRank:
        if self.xp_total >= 601:
            return PlayerRank.MASTER
        elif self.xp_total >= 301:
            return PlayerRank.EXPERT
        elif self.xp_total >= 101:
            return PlayerRank.SCOUT
        return PlayerRank.NEWBIE

    @property
    def rank_display(self) -> str:
        labels = {
            PlayerRank.NEWBIE: "Новачок",
            PlayerRank.SCOUT: "Слідопит",
            PlayerRank.EXPERT: "Знавець Залу",
            PlayerRank.MASTER: "Майстер Свіжості",
            PlayerRank.LEGEND: "Легенда",
        }
        return labels.get(self.rank, "Новачок")
