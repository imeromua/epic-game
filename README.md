# 🎮 EpicTeam Drive

> Корпоративна платформа гейміфікації для команди магазину.  
> Telegram MiniApp + FastAPI + PostgreSQL + Redis.

---

## Зміст

- [Концепція](#концепція)
- [Архітектура](#архітектура)
- [Технологічний стек](#технологічний-стек)
- [Структура проекту](#структура-проекту)
- [Швидкий старт](#швидкий-старт)
- [Змінні середовища](#змінні-середовища)
- [API Endpoints](#api-endpoints)
- [Механіки гри](#механіки-гри)
- [Ролі та авторизація](#ролі-та-авторизація)
- [Деплой](#деплой)

---

## Концепція

**EpicTeam Drive** — інструмент для стимулювання активності персоналу (12 співробітників) через ігрові механіки всередині Telegram.

| Мета | Механіка |
|---|---|
| Зменшення простроченої продукції | Photo-квести — «хто перший знайде товар з терміном 2 дні?» |
| Знання асортименту та цін | Knowledge Quiz з обмеженням часу |
| Щоденна залученість | Рандомні івенти, streak-система, таблиця лідерів |
| Мікро-винагороди | Магазин призів (бургер, кава, шоколад, доп. перерва) |

---

## Архітектура

```
┌──────────────────────────────────────────────────────┐
│                   Telegram Client                     │
│   ┌─────────────────────┐  ┌────────────────────┐    │
│   │    Bot Messages      │  │  MiniApp (React)   │    │
│   │  (сповіщення/квести) │  │  Dashboard / Quest │    │
│   └──────────┬──────────┘  └─────────┬──────────┘    │
└──────────────┼───────────────────────┼───────────────┘
               │                       │ HTTP + JWT
    ┌──────────▼───────────────────────▼──────────┐
    │              FastAPI (api:8000)               │
    │  /auth  /players  /quests  /prizes  /leaderboard │
    └──────────┬──────────────────┬────────────────┘
               │                  │
    ┌──────────▼──────┐  ┌────────▼────────┐
    │   PostgreSQL     │  │      Redis       │
    │  (дані, логи)    │  │ (First-Win lock  │
    └─────────────────┘  │  leaderboard,    │
                         │  стани квестів)  │
                         └─────────────────┘
```

**First-Win логіка** (атомарна, без race condition):
```python
winner = await redis.set(
    f"quest:{quest_id}:winner",
    user_id,
    nx=True,   # тільки якщо ключ не існує
    ex=3600
)
```

---

## Технологічний стек

| Шар | Технологія | Версія |
|---|---|---|
| **Бот** | aiogram | 3.20+ |
| **API** | FastAPI + Uvicorn | 0.115 / 0.34 |
| **БД** | PostgreSQL + SQLAlchemy (async) | 16 / 2.0 |
| **Міграції** | Alembic | 1.15 |
| **Черги / стани** | Redis + hiredis | 7 / 5.2 |
| **Планувальник** | APScheduler | 3.11 |
| **MiniApp** | React 18 + Vite 6 | — |
| **Сервер MiniApp** | Nginx (multi-stage Docker) | alpine |
| **Мова** | Python 3.11+ / JavaScript (ES2022) | — |
| **Контейнери** | Docker + docker-compose | — |

---

## Структура проекту

```
epic-game/
├── api/                        # FastAPI бекенд
│   ├── main.py                 # Точка входу, CORS, роутери
│   ├── alembic.ini             # Конфіг Alembic
│   ├── alembic/
│   │   ├── env.py              # Async-engine для міграцій
│   │   └── versions/           # SQL міграції
│   │       └── 20260429_001_initial_schema.py
│   ├── core/
│   │   ├── config.py           # Pydantic Settings (.env)
│   │   ├── database.py         # AsyncSession, Base
│   │   ├── redis.py            # Redis клієнт + ключі + First-Win lock
│   │   └── security.py         # JWT, Telegram initData validation
│   ├── models/
│   │   ├── player.py           # Player, PlayerRank enum
│   │   ├── quest.py            # Quest, QuestResult, enums
│   │   └── prize.py            # Prize, PrizeTransaction
│   ├── routers/
│   │   ├── auth.py             # POST /auth/signin
│   │   ├── players.py          # GET /players/me, /me/history
│   │   ├── quests.py           # CRUD квестів, відповіді, First-Win
│   │   ├── prizes.py           # Магазин призів, redemption
│   │   ├── leaderboard.py      # Місячний / тижневий рейтинг
│   │   └── admin.py            # Адмін: валідація фото, статистика
│   └── Dockerfile
│
├── bot/                        # Telegram бот
│   ├── main.py                 # Старт, Menu Button WebApp, команди
│   ├── handlers/
│   │   ├── start.py            # /start → MiniApp кнопка
│   │   ├── quest.py            # Розсилка квестів у групу
│   │   └── player.py           # /profile, /top
│   └── Dockerfile
│
├── scheduler/                  # APScheduler
│   ├── main.py                 # Запуск планувальника
│   └── jobs/
│       ├── random_events.py    # Рандомні квести (08:00–10:00)
│       └── monthly_reset.py    # Скидання місячного рейтингу
│
├── miniapp/                    # React MiniApp
│   ├── index.html              # Telegram WebApp SDK
│   ├── vite.config.js          # proxy /api → backend
│   ├── nginx.conf              # Production serve + gzip
│   ├── Dockerfile              # multi-stage: node → nginx
│   └── src/
│       ├── main.jsx            # Telegram themeParams → CSS vars
│       ├── App.jsx             # Auth init, routing, toast
│       ├── api.js              # Всі HTTP запити + JWT
│       ├── hooks/
│       │   └── useTelegram.js  # haptic, confirm, close
│       ├── styles/
│       │   └── globals.css     # Design system (~600 рядків)
│       ├── components/
│       │   ├── BottomNav.jsx   # 5 табів
│       │   ├── Spinner.jsx
│       │   └── Countdown.jsx   # Таймер з анімацією
│       └── pages/
│           ├── Dashboard.jsx   # Ранг, XP бар, активний квест
│           ├── QuestPage.jsx   # photo / text / choice відповіді
│           ├── Leaderboard.jsx # Подіум TOP-3 + список 4–12
│           ├── PrizeShop.jsx   # Магазин + мої призи
│           └── HistoryPage.jsx # Лог квестів та призів
│
├── docker-compose.yml          # 6 сервісів: db, redis, api, miniapp, bot, scheduler
├── .env.example                # Шаблон змінних середовища
└── requirements.txt            # Всі Python залежності
```

---

## Швидкий старт

### Вимоги
- Docker 24+ та docker-compose
- Telegram Bot Token ([BotFather](https://t.me/BotFather))
- Домен або ngrok для MiniApp URL (Telegram вимагає HTTPS)

### 1. Клонувати та налаштувати

```bash
git clone https://github.com/imeromua/epic-game.git
cd epic-game

cp .env.example .env
# Відкрити .env та заповнити всі значення (див. розділ нижче)
```

### 2. Запустити

```bash
docker compose up --build
# API: http://localhost:8000
# MiniApp: http://localhost:3000
# Docs: http://localhost:8000/docs
```

Alembic міграції накочуються **автоматично** при старті `api` сервісу.

### 3. Локальна розробка MiniApp

```bash
cd miniapp
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
# → http://localhost:5173
```

> **Dev-режим без Telegram:** MiniApp автоматично підставляє fake user якщо `Telegram.WebApp.initData` порожній.

---

## Змінні середовища

```env
# Telegram
BOT_TOKEN=             # токен бота від BotFather
MINIAPP_URL=           # HTTPS URL де хоститься miniapp

# PostgreSQL
POSTGRES_DB=epicteam
POSTGRES_USER=epicteam
POSTGRES_PASSWORD=     # strong password
DATABASE_URL=postgresql+asyncpg://epicteam:PASSWORD@db:5432/epicteam

# Redis
REDIS_URL=redis://redis:6379/0

# JWT (мінімум 32 символи)
JWT_SECRET=            # довгий випадковий рядок
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080   # 7 днів

# Додатково
ADMIN_TG_IDS=123456789,987654321   # Telegram ID адмінів
GROUP_CHAT_ID=-100xxxxxxxxxx        # ID групового чату команди
DEBUG=false
```

---

## API Endpoints

| Метод | Шлях | Опис |
|---|---|---|
| `POST` | `/auth/signin` | Авторизація через Telegram initData → JWT |
| `GET` | `/players/me` | Профіль поточного гравця |
| `GET` | `/players/me/history` | Хронологічний лог квестів та призів |
| `GET` | `/quests/active` | Поточний активний квест |
| `POST` | `/quests/{id}/answer` | Відповідь text/choice (First-Win) |
| `POST` | `/quests/{id}/photo` | Відправка фото-звіту |
| `GET` | `/prizes/` | Список призів магазину |
| `GET` | `/prizes/my-transactions` | Мої отримані призи |
| `POST` | `/prizes/{id}/redeem` | Обміняти XP на приз |
| `GET` | `/leaderboard/` | Місячний рейтинг |
| `GET` | `/leaderboard/weekly` | Тижневий рейтинг |

> Повна документація: `http://localhost:8000/docs` (Swagger UI)

---

## Механіки гри

### Ранги та XP

| Ранг | XP від | XP до | Emoji |
|---|---|---|---|
| Новачок | 0 | 100 | 🌱 |
| Слідопит | 100 | 300 | 🔍 |
| Знавець Залу | 300 | 600 | 🎯 |
| Майстер Свіжості | 600 | 1000 | ⭐ |
| Легенда | 1000+ | ∞ | 👑 |

### Типи квестів

| Тип | Опис | Підтвердження |
|---|---|---|
| **photo** | Знайти товар, зфотографувати | Адмін підтверджує фото |
| **text** | Вписати відповідь (ціна, локація) | Автоматично |
| **choice** | Так/Ні або варіанти | Автоматично |

### Anti-cheat

- EXIF timestamp фото перевіряється на дельту < 60 сек
- pHash дублікатів блокує повторне використання старих фото
- Redis `SET nx` гарантує атомарне присвоєння переможця

---

## Ролі та авторизація

| Роль | Можливості |
|---|---|
| `player` | Відповідати на квести, магазин, рейтинг, профіль |
| `admin` | + Створення квестів, валідація фото, статистика, видача призів |

**Авторизація:** `Telegram.WebApp.initData` → HMAC підпис перевіряється на бекенді → видається JWT (7 днів). Без паролів, без реєстрації.

---

## Деплой

### З доменом (рекомендовано)

```bash
# 1. Отримати SSL сертифікат
certbot certonly --standalone -d your-domain.com

# 2. Виставити в .env
MINIAPP_URL=https://your-domain.com

# 3. Запустити
docker compose up -d
```

### Ngrok (для тестування)

```bash
ngrok http 3000
# Скопіювати HTTPS URL → MINIAPP_URL в .env
```

> **Вимога Telegram:** MiniApp URL **обов'язково** має бути HTTPS.

---

## Ліцензія

MIT © 2026 EpicTeam Drive
