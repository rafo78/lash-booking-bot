from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from bot.keyboards.main_menu import get_main_menu
from database.database import async_session
from database.models import User


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    telegram_user = message.from_user

    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                role="client",
            )

            session.add(user)
            await session.commit()

            text = (
                "👋 Привет!\n\n"
                "Добро пожаловать в сервис записи "
                "к мастерам по наращиванию ресниц! ❤️\n\n"
                "Выбери нужный раздел:"
            )

        else:
            text = (
                f"👋 С возвращением, "
                f"{telegram_user.first_name or 'друг'}!\n\n"
                "Выбери нужный раздел:"
            )

    await message.answer(
        text,
        reply_markup=get_main_menu(),
    )