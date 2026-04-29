# 🎮 EpicTeam Drive

Корпоративна платформа гейміфікації для команди магазину.

## Концепція

- **Бот** — виключно сповіщення (нові квести, результати, призи)
- **MiniApp** — весь функціонал (квести, рейтинг, магазин XP, адмін-панель)
- **First-Win** механіка з Redis Distributed Lock
- **Три категорії** квестів і призів (⭐ / ⭐⭐ / ⭐⭐⭐)
- **💎 Легендарний квест** — раз на 3–4 місяці, приз 1000+ ₴

## Стек

| Шар | Технологія |
|---|---|
| Бот | Python 3.11+, aiogram 3.x |
| API | FastAPI + Uvicorn |
| База даних | PostgreSQL + psycopg2 |
| Черги / стани | Redis |
| Планувальник | APScheduler |
| MiniApp | React + TypeScript |
| Контейнери | Docker + docker-compose |

## Структура проекту

```
epic-game/
├── bot/                  # Telegram бот (лише сповіщення)
│   ├── main.py
│   ├── notifications/    # Модулі відправки повідомлень
│   └── keyboards/        # InlineKeyboard з WebApp кнопками
├── api/                  # FastAPI бекенд
│   ├── main.py
│   ├── routers/          # Ендпоінти
│   ├── models/           # SQLAlchemy моделі
│   ├── schemas/          # Pydantic схеми
│   ├── services/         # Бізнес-логіка
│   └── core/             # Конфіг, БД, Redis, безпека
├── scheduler/            # APScheduler задачі
│   ├── main.py
│   └── jobs/
├── miniapp/              # React фронтенд
│   ├── src/
│   │   ├── pages/        # Dashboard, Quest, Leaderboard, Prizes, Admin
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/          # API клієнт
│   │   └── store/        # Zustand стани
│   └── public/
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Швидкий старт

```bash
# 1. Клонувати
git clone https://github.com/imeromua/epic-game.git
cd epic-game

# 2. Налаштувати змінні середовища
cp .env.example .env
# Заповнити .env своїми значеннями

# 3. Запустити
docker-compose up -d
```

## Ролі

- `player` — звичайний співробітник
- `admin` — майстер квестів (керівник)

Авторизація через `Telegram.WebApp.initData` — без паролів.
