from sqlalchemy import Integer, String, Text, Enum as SAEnum, DateTime, ForeignKey, Interval
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from api.core.database import Base
import enum


class QuestCategory(int, enum.Enum):
    EASY = 1       # ⭐    просте
    MEDIUM = 2     # ⭐⭐   середнє
    HARD = 3       # ⭐⭐⭐  складне
    LEGENDARY = 4  # 💎   легендарне


class QuestType(str, enum.Enum):
    PHOTO = "photo"       # Фото-звіт
    TEXT = "text"         # Текстова відповідь
    CHOICE = "choice"     # Вибір варіанту


class QuestStatus(str, enum.Enum):
    PENDING = "pending"       # Де запущений (заплановано)
    ACTIVE = "active"         # Активний (вікно відкрито)
    CLOSED = "closed"         # Закрито (є переможець)
    EXPIRED = "expired"       # Таймаут (ніхто не відповів)
    CANCELLED = "cancelled"   # Скасовано адміном


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Зміст
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[QuestCategory] = mapped_column(
        SAEnum(QuestCategory, values_callable=lambda x: [str(e.value) for e in x]),
        nullable=False
    )
    quest_type: Mapped[QuestType] = mapped_column(SAEnum(QuestType), nullable=False)

    # Відповідь (для текстових та вибір)
    correct_answer: Mapped[str | None] = mapped_column(Text)        # еталон
    answer_options: Mapped[str | None] = mapped_column(Text)        # JSON рядок

    # Налаштування
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=5)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_participation: Mapped[int] = mapped_column(Integer, default=10)

    # Приз (визначається авто при старті)
    prize_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("prizes.id"))
    prize: Mapped["Prize | None"] = relationship("Prize")  # type: ignore

    # Управління часом
    status: Mapped[QuestStatus] = mapped_column(
        SAEnum(QuestStatus), default=QuestStatus.PENDING
    )
    scheduled_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    # Telegram
    tg_message_id: Mapped[int | None] = mapped_column(BigInteger)  # для edit_message

    # Анонс
    announce_30min: Mapped[bool] = mapped_column(default=False)
    announce_5min: Mapped[bool] = mapped_column(default=False)
    announce_text_30: Mapped[str | None] = mapped_column(Text)
    announce_text_5: Mapped[str | None] = mapped_column(Text)

    # Шаблон
    is_template: Mapped[bool] = mapped_column(default=False)
    template_name: Mapped[str | None] = mapped_column(String(128))

    # Створив (FK на players додаємо після)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Зв’язки
    results: Mapped[list["QuestResult"]] = relationship(back_populates="quest")


class QuestResult(Base):
    """Oднин запис = одна участь гравця у квесті"""
    __tablename__ = "quest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_id: Mapped[int] = mapped_column(Integer, ForeignKey("quests.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)

    is_winner: Mapped[bool] = mapped_column(default=False)
    answer_text: Mapped[str | None] = mapped_column(Text)
    photo_file_id: Mapped[str | None] = mapped_column(String(256))  # Telegram file_id
    photo_hash: Mapped[str | None] = mapped_column(String(64))      # pHash анти-фрод
    time_to_win: Mapped[Interval | None] = mapped_column(Interval)  # ключова метрика
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)

    # Валідація фото (admin)
    photo_validated: Mapped[bool | None] = mapped_column()          # None = пендінг
    validated_by: Mapped[int | None] = mapped_column(Integer)       # player_id адміна
    validated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    submitted_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Зв’язки
    quest: Mapped[Quest] = relationship(back_populates="results")
    player: Mapped["Player"] = relationship(back_populates="quest_results")  # type: ignore


from sqlalchemy import BigInteger  # noqa (used above)
from api.models.prize import Prize  # noqa
