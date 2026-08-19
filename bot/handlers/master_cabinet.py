from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import select

from bot.keyboards.main_menu import get_main_menu
from bot.keyboards.master_menu import get_master_menu
from database.database import async_session
from database.models import User


router = Router()

MASTER_CABINET_BUTTON = "👩‍💼 Кабинет мастера"
BACK_TO_MAIN_MENU_BUTTON = "🔙 Главное меню"
IN_DEVELOPMENT_BUTTONS = {
    "📅 Мои записи",
    "👥 Мои клиенты",
    "💅 Мои услуги",
    "🕐 Расписание",
    "⚙️ Настройки",
}


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()


@router.message(F.text == MASTER_CABINET_BUTTON)
async def master_cabinet_handler(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)

    if user is None or user.role != "master":
        await message.answer(
            "⛔ Доступ к кабинету мастера запрещён."
        )
        return

    await message.answer(
        "👩‍💼 Кабинет мастера",
        reply_markup=get_master_menu(),
    )


@router.message(F.text == BACK_TO_MAIN_MENU_BUTTON)
async def back_to_main_menu_handler(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    role = user.role if user is not None else "client"

    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu(role),
    )


@router.message(F.text.in_(IN_DEVELOPMENT_BUTTONS))
async def master_section_in_development_handler(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)

    if user is None or user.role != "master":
        await message.answer(
            "⛔ Доступ к кабинету мастера запрещён."
        )
        return

    await message.answer(
        "Раздел находится в разработке"
    )
