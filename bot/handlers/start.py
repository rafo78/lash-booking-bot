from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select

from bot.keyboards.main_menu import get_main_menu
from database.database import async_session
from database.models import User, Booking, Master, Service


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
@router.message(F.text == "📋 Мои записи")
async def my_bookings_handler(message: Message):
    telegram_user = message.from_user

    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "Сначала нажмите /start."
            )
            return

        result = await session.execute(
            select(Booking, Master, Service)
            .join(
                Master,
                Booking.master_id == Master.id,
            )
            .join(
                Service,
                Booking.service_id == Service.id,
            )
            .where(
                Booking.user_id == user.id,
                Booking.status == "confirmed",
            )
            .order_by(
                Booking.booking_date,
                Booking.booking_time,
            )
        )

        bookings = result.all()

    if not bookings:
        await message.answer(
            "📋 <b>Мои записи</b>\n\n"
            "У вас пока нет активных записей.",
            parse_mode="HTML",
        )
        return

    text = "📋 <b>Мои записи</b>\n\n"

    for booking, master, service in bookings:
        text += (
            f"💗 <b>{service.name}</b>\n"
            f"👩 Мастер: {master.name}\n"
            f"📅 Дата: {booking.booking_date}\n"
            f"🕐 Время: {booking.booking_time}\n"
            f"💰 Цена: {booking.price} ₽\n\n"
        )

    for booking, master, service in bookings:
        await message.answer(
            "📋 <b>Моя запись</b>\n\n"
            f"💗 <b>{service.name}</b>\n"
            f"👩 Мастер: {master.name}\n"
            f"📅 Дата: {booking.booking_date}\n"
            f"🕐 Время: {booking.booking_time}\n"
            f"💰 Цена: {booking.price} ₽\n"
            f"{'💡 LED-наращивание +200 ₽' if booking.led else ''}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ Отменить запись",
                            callback_data=(
                                f"booking_cancel:{booking.id}"
                            ),
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )