from datetime import date, datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from bot.keyboards.master_menu import get_master_menu
from database.database import async_session
from database.models import User, Booking, Service


router = Router()


@router.message(F.text == "👩‍💼 Кабинет мастера")
async def master_cabinet(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

    if user is None or user.role != "master":
        await message.answer(
            "⛔ У вас нет доступа к кабинету мастера."
        )
        return

    await message.answer(
        "👩‍💼 <b>Кабинет мастера</b>\n\n"
        "Добро пожаловать, Полечка! 💗\n\n"
        "Здесь будут доступны функции мастера:\n\n"
        "📅 Мои записи\n"
        "👥 Мои клиенты\n"
        "💅 Мои услуги\n"
        "🕐 Расписание\n"
        "⚙️ Настройки",
        parse_mode="HTML",
        reply_markup=get_master_menu(),
    )
def format_date(value: date) -> str:
    months = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]

    return f"{value.day} {months[value.month - 1]}"


@router.message(F.text == "📅 Мои записи")
async def master_bookings(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None or user.role != "master":
            await message.answer(
                "⛔ У вас нет доступа к этому разделу."
            )
            return

        result = await session.execute(
            select(Booking)
            .where(
                Booking.master_id == 1,
                Booking.status == "confirmed",
            )
            .order_by(
                Booking.booking_date,
                Booking.booking_time,
            )
        )

        bookings = result.scalars().all()

        if not bookings:
            await message.answer(
                "📅 <b>Мои записи</b>\n\n"
                "На данный момент записей нет.",
                parse_mode="HTML",
            )
            return

        for booking in bookings:
            result = await session.execute(
                select(User).where(
                    User.id == booking.user_id
                )
            )
            client = result.scalar_one_or_none()

            result = await session.execute(
                select(Service).where(
                    Service.id == booking.service_id
                )
            )
            service = result.scalar_one_or_none()

            client_name = (
                client.first_name
                if client and client.first_name
                else "Клиент"
            )

            service_name = (
                service.name
                if service
                else "Неизвестная услуга"
            )

            booking_date = date.fromisoformat(
                booking.booking_date
            )

            end_time = (
                datetime.strptime(
                    booking.booking_time,
                    "%H:%M",
                )
                + timedelta(
                    minutes=booking.duration_min
                )
            ).strftime("%H:%M")

            led_text = " + LED" if booking.led else ""

            await message.answer(
                "📅 <b>Запись</b>\n\n"
                f"👤 Клиент: <b>{client_name}</b>\n"
                f"💅 Услуга: <b>{service_name}</b>{led_text}\n"
                f"📅 Дата: <b>{format_date(booking_date)}</b>\n"
                f"🕐 Время: <b>{booking.booking_time}–{end_time}</b>\n"
                f"💰 Цена: <b>{booking.price} ₽</b>",
                parse_mode="HTML",
            )
@router.message(F.text == "👥 Мои клиенты")
async def master_clients(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.role == "client",
                User.id.in_(
                    select(Booking.user_id).where(
                        Booking.master_id == 1
                    )
                ),
            )
        )

        clients = result.scalars().all()

        if not clients:
            await message.answer(
                "👥 <b>Мои клиенты</b>\n\n"
                "У вас пока нет клиентов.",
                parse_mode="HTML",
            )
            return

        text = "👥 <b>Мои клиенты</b>\n\n"

        for client in clients:
            name = client.first_name or "Без имени"

            if client.username:
                username = f"@{client.username}"
            else:
                username = "нет username"

            text += (
                f"👤 <b>{name}</b>\n"
                f"Telegram: {username}\n\n"
            )

        await message.answer(
            text,
            parse_mode="HTML",
        )
@router.message(F.text == "💅 Мои услуги")
async def master_services(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Service)
            .where(
                Service.master_id == 1,
                Service.is_active == True,
            )
            .order_by(
                Service.category,
                Service.name,
            )
        )

        services = result.scalars().all()

        if not services:
            await message.answer(
                "💅 <b>Мои услуги</b>\n\n"
                "У вас пока нет активных услуг.",
                parse_mode="HTML",
            )
            return

        text = "💅 <b>Мои услуги</b>\n\n"

        current_category = None

        for service in services:
            if service.category != current_category:
                current_category = service.category

                text += (
                    f"\n<b>{current_category}</b>\n"
                )

            if service.price_from == service.price_to:
                price = f"{service.price_from} ₽"
            else:
                price = (
                    f"{service.price_from}–"
                    f"{service.price_to} ₽"
                )

            if service.duration_min == service.duration_max:
                duration = f"{service.duration_min} мин"
            else:
                duration = (
                    f"{service.duration_min}–"
                    f"{service.duration_max} мин"
                )

            text += (
                f"💅 {service.name}\n"
                f"   💰 {price}\n"
                f"   🕐 {duration}\n\n"
            )

        await message.answer(
            text,
            parse_mode="HTML",
        )
@router.message(F.text == "🕐 Расписание")
async def master_schedule(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None or user.role != "master":
            await message.answer(
                "⛔ Доступ к расписанию запрещён."
            )
            return

        result = await session.execute(
            select(Booking)
            .where(
                Booking.master_id == 1,
                Booking.status == "confirmed",
            )
            .order_by(
                Booking.booking_date,
                Booking.booking_time,
            )
        )

        bookings = result.scalars().all()

        text = (
            "🕐 <b>Расписание</b>\n\n"
            "👩 Мастер: <b>Полечка</b>\n"
            "📍 Рязань, ул. Чапаева, 59\n"
            "🕐 Рабочее время: <b>10:00–20:00</b>\n\n"
        )

        if not bookings:
            text += "📅 Записей пока нет."
        else:
            text += "📅 <b>Записи:</b>\n\n"

            for booking in bookings:
                result = await session.execute(
                    select(User).where(
                        User.id == booking.user_id
                    )
                )
                client = result.scalar_one_or_none()

                result = await session.execute(
                    select(Service).where(
                        Service.id == booking.service_id
                    )
                )
                service = result.scalar_one_or_none()

                client_name = (
                    client.first_name
                    if client and client.first_name
                    else "Неизвестный клиент"
                )

                service_name = (
                    service.name
                    if service
                    else "Неизвестная услуга"
                )

                booking_date = date.fromisoformat(
                    booking.booking_date
                )

                end_time = (
                    datetime.strptime(
                        booking.booking_time,
                        "%H:%M",
                    )
                    + timedelta(
                        minutes=booking.duration_min
                    )
                ).strftime("%H:%M")

                text += (
                    f"📅 <b>{format_date(booking_date)}</b>\n"
                    f"🕐 {booking.booking_time}–{end_time}\n"
                    f"👤 {client_name}\n"
                    f"💅 {service_name}\n\n"
                )

        await message.answer(
            text,
            parse_mode="HTML",
        )
@router.message(F.text == "⚙️ Настройки")
async def master_settings(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None or user.role != "master":
            await message.answer(
                "⛔ Доступ к настройкам запрещён."
            )
            return

        text = (
            "⚙️ <b>Настройки мастера</b>\n\n"
            "👩 Имя: <b>Полечка</b>\n"
            "📍 Город: <b>Рязань</b>\n"
            "🏠 Адрес: <b>ул. Чапаева, 59</b>\n"
            "🕐 Рабочее время: <b>10:00–20:00</b>\n\n"
            "ℹ️ Изменение настроек пока недоступно."
        )

        await message.answer(
            text,
            parse_mode="HTML",
        )