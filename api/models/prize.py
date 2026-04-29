from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from api.core.database import Base
import enum


class PrizeCategory(int, enum.Enum):
    EASY = 1       # ⭐   до 30 ₴  | 100 XP
    MEDIUM = 2     # ⭐⭐  до 120 ₴ | 300 XP
    HARD = 3       # ⭐⭐⭐ до 300 ₴ | 600 XP
    LEGENDARY = 4  # 💎  1000+ ₴  | special


class PrizeType(str, enum.Enum):
    MATERIAL = "material"         # Фізичний предмет
    NON_MATERIAL = "non_material" # Нематеріальний (перерва, вибір зміни)
    XP_SHOP = "xp_shop"          # Через XP-магазин


class Prize(Base):
    __tablename__ = "prizes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    emoji: Mapped[str] = mapped_column(String(8), default="🎁")

    category: Mapped[PrizeCategory] = mapped_column(
        SAEnum(PrizeCategory, values_callable=lambda x: [str(e.value) for e in x]),
        nullable=False
    )
    prize_type: Mapped[PrizeType] = mapped_column(SAEnum(PrizeType), default=PrizeType.MATERIAL)

    # Жахування (для зваженої рандомізації)
    weight: Mapped[int] = mapped_column(Integer, default=30)  # базова вага 30

    # Бюджет
    cost_uah: Mapped[int] = mapped_column(Integer, default=0)   # собівартість в грн
    xp_cost: Mapped[int] = mapped_column(Integer, default=0)    # ціна в XP магазині

    # Сток
    stock: Mapped[int | None] = mapped_column(Integer)          # None = нескінченний
    stock_monthly_limit: Mapped[int | None] = mapped_column(Integer)  # ліміт/місяць

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_rare: Mapped[bool] = mapped_column(Boolean, default=False)  # рідкісний → окреме повідомлення

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transactions: Mapped[list["PrizeTransaction"]] = relationship(back_populates="prize")


class PrizeTransaction(Base):
    """Aудит видачі призів — кожна видача фіксується"""
    __tablename__ = "prize_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)
    prize_id: Mapped[int] = mapped_column(Integer, ForeignKey("prizes.id"), nullable=False)
    quest_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("quests.id"))

    # QR-код
    qr_token: Mapped[str] = mapped_column(String(64), unique=True)  # UUID токен
    qr_expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    is_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    issued_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"))  # admin
    issued_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    # Тип отримання
    source: Mapped[str] = mapped_column(String(32), default="quest")  # quest | xp_shop

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    player: Mapped["Player"] = relationship(back_populates="prize_transactions", foreign_keys=[player_id])  # type: ignore
    prize: Mapped[Prize] = relationship(back_populates="transactions")
