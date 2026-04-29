from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import httpx

from bot.core.config import bot_settings

router = Router()


class QuestCreateFSM(StatesGroup):
    title = State()
    description = State()
    category = State()
    quest_type = State()
    time_limit = State()
    confirm = State()


# Фільтр: тільки адміни у приватному чаті
def is_admin(message: Message) -> bool:
    # Додаткова перевірка по API відбувається в handler-ах
    return message.chat.type == "private"


@router.message(Command("newquest"))
async def cmd_new_quest(message: Message, state: FSMContext, api: httpx.AsyncClient):
    """Початок FSM-конструктора квесту"""
    # Перевірка ролі
    resp = await api.get(f"/players/by-tg/{message.from_user.id}")
    if resp.status_code != 200 or not resp.json().get("is_admin"):
        return

    await state.set_state(QuestCreateFSM.title)
    await message.answer(
        "📝 <b>Конструктор квесту</b>\n\n"
        "Напишіть <b>назву</b> квесту:"
    )


@router.message(QuestCreateFSM.title)
async def fsm_quest_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(QuestCreateFSM.description)
    await message.answer("Тепер <b>опис</b> квесту (що саме шукати/робити):")


@router.message(QuestCreateFSM.description)
async def fsm_quest_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(QuestCreateFSM.category)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ Легко (50 XP)", callback_data="cat_1"),
            InlineKeyboardButton(text="⭐⭐ Середнє (120 XP)", callback_data="cat_2"),
        ],
        [
            InlineKeyboardButton(text="⭐⭐⭐ Складно (250 XP)", callback_data="cat_3"),
            InlineKeyboardButton(text="💎 Легенда (1000 XP)", callback_data="cat_4"),
        ],
    ])
    await message.answer("Виберіть <b>категорію</b>:", reply_markup=kb)


@router.callback_query(F.data.startswith("cat_"), QuestCreateFSM.category)
async def fsm_quest_category(callback: CallbackQuery, state: FSMContext):
    cat = int(callback.data.split("_")[1])
    await state.update_data(category=cat)
    await state.set_state(QuestCreateFSM.quest_type)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 Фото-квест", callback_data="type_photo"),
            InlineKeyboardButton(text="✏️ Текстова відповідь", callback_data="type_text"),
        ],
    ])
    await callback.message.edit_text("Тип квесту:", reply_markup=kb)


@router.callback_query(F.data.startswith("type_"), QuestCreateFSM.quest_type)
async def fsm_quest_type(callback: CallbackQuery, state: FSMContext):
    qtype = callback.data.split("_", 1)[1]
    await state.update_data(quest_type=qtype)
    await state.set_state(QuestCreateFSM.time_limit)
    await callback.message.edit_text("Час виконання (хвилини, 2-10):")


@router.message(QuestCreateFSM.time_limit)
async def fsm_quest_time(message: Message, state: FSMContext, api: httpx.AsyncClient):
    try:
        minutes = int(message.text.strip())
        minutes = max(2, min(60, minutes))
    except ValueError:
        await message.answer("Введіть число від 2 до 60")
        return

    data = await state.get_data()
    data["time_limit_minutes"] = minutes

    # Створюємо квест через API
    xp_map = {1: 50, 2: 120, 3: 250, 4: 1000}
    payload = {
        "title": data["title"],
        "description": data["description"],
        "category": data["category"],
        "quest_type": data["quest_type"],
        "time_limit_minutes": minutes,
        "xp_reward": xp_map[data["category"]],
        "start_now": True,
    }

    resp = await api.post(
        "/admin/quests",
        json=payload,
        headers={"X-TG-ID": str(message.from_user.id)},
    )

    await state.clear()

    if resp.status_code == 200:
        quest = resp.json()
        await message.answer(
            f"✅ Квест <b>«{quest['title']}»</b> запущено!\n"
            f"⏰ Час: {minutes} хв.\n"
            f"⚡ Гравці вже отримали повідомлення."
        )
    else:
        await message.answer(f"Помилка: {resp.text}")


@router.message(Command("validate"))
async def cmd_validate(message: Message, api: httpx.AsyncClient):
    """Показує пендінг-фото для валідації адміном"""
    resp = await api.get(
        "/admin/pending-photos",
        headers={"X-TG-ID": str(message.from_user.id)},
    )
    if resp.status_code != 200:
        return

    items = resp.json()
    if not items:
        await message.answer("Немає фото для перевірки ✅")
        return

    for item in items[:5]:  # показуємо перші 5
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Підтвердити",
                callback_data=f"approve_{item['result_id']}"
            ),
            InlineKeyboardButton(
                text="❌ Відхилити",
                callback_data=f"reject_{item['result_id']}"
            ),
        ]])
        await message.answer_photo(
            photo=item["photo_file_id"],
            caption=f"👤 {item['player_name']}\n🎯 {item['quest_title']}",
            reply_markup=kb,
        )


@router.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def handle_photo_validation(callback: CallbackQuery, api: httpx.AsyncClient):
    action, result_id = callback.data.split("_", 1)
    approved = (action == "approve")

    resp = await api.post(
        f"/admin/validate-photo/{result_id}",
        json={"approved": approved},
        headers={"X-TG-ID": str(callback.from_user.id)},
    )

    if resp.status_code == 200:
        icon = "✅" if approved else "❌"
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n{icon} Оброблено"
        )
    await callback.answer()
