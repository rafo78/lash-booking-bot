from datetime import date, datetime, timedelta

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select

from database.database import async_session
from database.models import Master, Service, User, Booking


router = Router()


# ============================================================
# 📅 НАЧАЛО ЗАПИСИ
# ============================================================

@router.message(F.text == "📅 Записаться")
async def booking_start(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Master)
            .where(Master.is_active.is_(True))
            .order_by(Master.id)
        )

        masters = result.scalars().all()

    if not masters:
        await message.answer(
            "😔 Сейчас нет доступных мастеров."
        )
        return

    keyboard = []

    for master in masters:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"💗 {master.name}",
                    callback_data=f"booking_master:{master.id}",
                )
            ]
        )

    await message.answer(
        "📅 <b>Запись</b>\n\n"
        "Выберите мастера:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )


# ============================================================
# 👩 ВЫБОР МАСТЕРА
# ============================================================

@router.callback_query(F.data.startswith("booking_master:"))
async def booking_master(callback: CallbackQuery):
    master_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(
            select(Master).where(
                Master.id == master_id,
                Master.is_active.is_(True),
            )
        )

        master = result.scalar_one_or_none()

        if master is None:
            await callback.answer(
                "Мастер не найден.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Service.category)
            .where(
                Service.master_id == master.id,
                Service.is_active.is_(True),
            )
            .distinct()
        )

        categories = result.scalars().all()

    if not categories:
        await callback.message.edit_text(
            "😔 У этого мастера пока нет доступных услуг."
        )
        await callback.answer()
        return

    category_titles = {
        "Коррекция": "💗 Коррекция",
        "Наращивание": "💕 Наращивание",
        "Снятие": "🖤 Снятие",
    }

    category_order = [
        "Коррекция",
        "Наращивание",
        "Снятие",
    ]

    keyboard = []

    for category in category_order:
        if category in categories:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=category_titles.get(
                            category,
                            category,
                        ),
                        callback_data=(
                            f"booking_category:"
                            f"{master.id}:"
                            f"{category}"
                        ),
                    )
                ]
            )

    await callback.message.edit_text(
        f"💗 <b>Мастер: {master.name}</b>\n\n"
        "Выберите категорию услуги:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# 💅 ВЫБОР КАТЕГОРИИ
# ============================================================

@router.callback_query(F.data.startswith("booking_category:"))
async def booking_category(callback: CallbackQuery):
    _, master_id, category = callback.data.split(":", 2)

    master_id = int(master_id)

    async with async_session() as session:
        result = await session.execute(
            select(Service)
            .where(
                Service.master_id == master_id,
                Service.category == category,
                Service.is_active.is_(True),
            )
            .order_by(Service.id)
        )

        services = result.scalars().all()

        result = await session.execute(
            select(Master).where(
                Master.id == master_id
            )
        )

        master = result.scalar_one_or_none()

    if not services or master is None:
        await callback.answer(
            "Услуги не найдены.",
            show_alert=True,
        )
        return

    keyboard = []

    for service in services:
        price = format_price(
            service.price_from,
            service.price_to,
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{service.name} — {price} ₽",
                    callback_data=(
                        f"booking_service:{service.id}"
                    ),
                )
            ]
        )

    category_titles = {
        "Коррекция": "💗 Коррекция",
        "Наращивание": "💕 Наращивание",
        "Снятие": "🖤 Снятие",
    }

    await callback.message.edit_text(
        f"💗 <b>{master.name}</b>\n"
        f"<b>{category_titles.get(category, category)}</b>\n\n"
        "Выберите услугу:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# 💅 ВЫБОР УСЛУГИ
# ============================================================

@router.callback_query(F.data.startswith("booking_service:"))
async def booking_service(callback: CallbackQuery):
    service_id = int(
        callback.data.split(":", 1)[1]
    )

    async with async_session() as session:
        result = await session.execute(
            select(Service).where(
                Service.id == service_id,
                Service.is_active.is_(True),
            )
        )

        service = result.scalar_one_or_none()

    if service is None:
        await callback.answer(
            "Услуга не найдена.",
            show_alert=True,
        )
        return

    price = format_price(
        service.price_from,
        service.price_to,
    )

    duration = format_duration(
        service.duration_min
    )

    await callback.message.edit_text(
        "📅 <b>Вы выбрали услугу</b>\n\n"
        f"💅 {service.name}\n"
        f"💰 Цена: {price} ₽\n"
        f"⏱ Время: {duration}\n\n"
        "📅 <b>Выберите дату:</b>",
        reply_markup=build_date_keyboard(service.id),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# 📅 КАЛЕНДАРЬ
# ============================================================

def build_date_keyboard(
    service_id: int,
    days: int = 14,
) -> InlineKeyboardMarkup:

    today = date.today()

    weekday_names = [
        "Пн",
        "Вт",
        "Ср",
        "Чт",
        "Пт",
        "Сб",
        "Вс",
    ]

    buttons = []

    for offset in range(days):
        current_date = today + timedelta(days=offset)

        text = (
            f"{weekday_names[current_date.weekday()]} "
            f"{current_date.day:02d}."
            f"{current_date.month:02d}"
        )

        buttons.append(
            InlineKeyboardButton(
                text=text,
                callback_data=(
                    f"booking_date:"
                    f"{service_id}:"
                    f"{current_date.isoformat()}"
                ),
            )
        )

    keyboard = []

    for i in range(0, len(buttons), 2):
        keyboard.append(
            buttons[i:i + 2]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


# ============================================================
# 📅 ВЫБОР ДАТЫ → СВОБОДНОЕ ВРЕМЯ
# ============================================================

@router.callback_query(F.data.startswith("booking_date:"))
async def booking_date(callback: CallbackQuery):
    _, service_id, selected_date = callback.data.split(":", 2)

    service_id = int(service_id)

    selected = date.fromisoformat(selected_date)

    if selected < date.today():
        await callback.answer(
            "Нельзя выбрать прошедшую дату.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        result = await session.execute(
            select(Service).where(
                Service.id == service_id,
                Service.is_active.is_(True),
            )
        )

        service = result.scalar_one_or_none()

        if service is None:
            await callback.answer(
                "Услуга не найдена.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Master).where(
                Master.id == service.master_id,
                Master.is_active.is_(True),
            )
        )

        master = result.scalar_one_or_none()

        if master is None:
            await callback.answer(
                "Мастер не найден.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Booking).where(
                Booking.master_id == master.id,
                Booking.booking_date == selected_date,
                Booking.status.in_(
                    ["confirmed", "pending"]
                ),
            )
        )

        bookings = result.scalars().all()

    slots = build_free_slots(
        master=master,
        service=service,
        selected_date=selected,
        bookings=bookings,
    )

    if not slots:
        await callback.message.edit_text(
            "😔 <b>Свободного времени нет.</b>\n\n"
            f"📅 Дата: {format_date(selected)}\n\n"
            "Пожалуйста, выберите другой день.",
            reply_markup=build_date_keyboard(
                service.id
            ),
            parse_mode="HTML",
        )

        await callback.answer()
        return

    keyboard = []

    row = []

    for slot_start, slot_end in slots:
        row.append(
            InlineKeyboardButton(
                text=f"🕐 {slot_start}",
                callback_data=(
                    f"booking_time:"
                    f"{service.id}:"
                    f"{selected_date}:"
                    f"{slot_start}:00"
                ),
            )
        )

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ Выбрать другую дату",
                callback_data=f"booking_back_date:{service.id}",
            )
        ]
    )

    await callback.message.edit_text(
        "🕐 <b>Свободное время</b>\n\n"
        f"💅 {service.name}\n"
        f"📅 {format_date(selected)}\n"
        f"⏱ {format_duration(service.duration_min)}\n\n"
        "Выберите время начала:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# ⬅️ НАЗАД К ДАТАМ
# ============================================================

@router.callback_query(F.data.startswith("booking_back_date:"))
async def booking_back_date(callback: CallbackQuery):
    service_id = int(
        callback.data.split(":", 1)[1]
    )

    await callback.message.edit_text(
        "📅 <b>Выберите дату:</b>",
        reply_markup=build_date_keyboard(
            service_id
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# 🕐 ВЫБОР ВРЕМЕНИ → ПОДТВЕРЖДЕНИЕ
# ============================================================

@router.callback_query(F.data.startswith("booking_time:"))
async def booking_time(callback: CallbackQuery):
    _, service_id, selected_date, time_and_led = (
        callback.data.split(":", 3)
    )

    start_time, led_value = time_and_led.rsplit(":", 1)

    led = led_value == "1"

    service_id = int(service_id)

    async with async_session() as session:
        result = await session.execute(
            select(Service).where(
                Service.id == service_id,
                Service.is_active.is_(True),
            )
        )

        service = result.scalar_one_or_none()

        if service is None:
            await callback.answer(
                "Услуга не найдена.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Master).where(
                Master.id == service.master_id
            )
        )

        master = result.scalar_one_or_none()

    start = datetime.strptime(
        start_time,
        "%H:%M",
    )

    end = start + timedelta(
        minutes=service.duration_min
    )

    await callback.message.edit_text(
        "📋 <b>Проверьте запись</b>\n\n"
        f"👩 Мастер: <b>{master.name}</b>\n"
        f"💅 Услуга: <b>{service.name}</b>\n"
        f"📅 Дата: <b>{format_date(date.fromisoformat(selected_date))}</b>\n"
        f"🕐 Время: <b>{start_time}–{end.strftime('%H:%M')}</b>\n"
        f"💰 Цена: <b>{format_price(service.price_from, service.price_to)} ₽</b>\n\n"
        "Подтвердить запись?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💡 LED +200 ₽",
                        callback_data=(
                           f"booking_confirm:"
                           f"{service.id}:"
                           f"{selected_date}:"
                           f"{start_time}:1"
                       ), 
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="✨ Без LED",
                        callback_data=(
                            f"booking_confirm:"
                            f"{service.id}:"
                            f"{selected_date}:"
                            f"{start_time}:0"
                    ),
                        ),
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Выбрать другое время",
                        callback_data=(
                            f"booking_date:"
                            f"{service.id}:"
                            f"{selected_date}"
                        ),
                    )
                ],
            ]
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# ✅ ПОДТВЕРЖДЕНИЕ И СОХРАНЕНИЕ ЗАПИСИ
# ============================================================

@router.callback_query(F.data.startswith("booking_confirm:"))
async def booking_confirm(callback: CallbackQuery):
    _, service_id, selected_date, time_and_led = (
        callback.data.split(":", 3)
    )

    start_time, led_value = time_and_led.rsplit(":", 1)

    led = led_value == "1"

    service_id = int(service_id)

    async with async_session() as session:
        result = await session.execute(
            select(Service).where(
                Service.id == service_id,
                Service.is_active.is_(True),
            )
        )

        service = result.scalar_one_or_none()

        if service is None:
            await callback.answer(
                "Услуга больше недоступна.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Master).where(
                Master.id == service.master_id,
                Master.is_active.is_(True),
            )
        )

        master = result.scalar_one_or_none()

        if master is None:
            await callback.answer(
                "Мастер не найден.",
                show_alert=True,
            )
            return

        start = datetime.strptime(
            start_time,
            "%H:%M",
        )

        end = start + timedelta(
            minutes=service.duration_min
        )

        end_time = end.strftime("%H:%M")

        # Повторно проверяем, не занял ли кто-то это время
        result = await session.execute(
            select(Booking).where(
                Booking.master_id == master.id,
                Booking.booking_date == selected_date,
                Booking.status.in_(
                    ["confirmed", "pending"]
                ),
            )
        )

        existing_bookings = result.scalars().all()

        if has_overlap(
            start_time=start_time,
            end_time=end_time,
            bookings=existing_bookings,
        ):
            await callback.answer(
                "😔 Это время уже заняли. Выберите другое.",
                show_alert=True,
            )

            await callback.message.edit_text(
                "😔 <b>Это время уже заняли.</b>\n\n"
                "Пожалуйста, выберите другое время.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🕐 Выбрать другое время",
                                callback_data=(
                                    f"booking_date:"
                                    f"{service.id}:"
                                    f"{selected_date}"
                                ),
                            )
                        ]
                    ]
                ),
                parse_mode="HTML",
            )

            return

        # Ищем клиента
        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                role="client",
            )

            session.add(user)


        await session.flush()

        booking_price = service.price_from + (200 if led else 0)
        booking = Booking(
            user_id=user.id,
            master_id=master.id,
            service_id=service.id,
            booking_date=selected_date,
            booking_time=start_time,
            duration_min=service.duration_min,
            price=booking_price,
            led=led,
            status="confirmed",
        )
        session.add(booking)

        await session.commit()

    await callback.message.edit_text(
        "🎉 <b>Запись подтверждена!</b>\n\n"
        f"👩 Мастер: <b>{master.name}</b>\n"
        f"💅 Услуга: <b>{service.name}</b>\n"
        f"📅 Дата: <b>{format_date(date.fromisoformat(selected_date))}</b>\n"
        f"🕐 Время: <b>{start_time}–{end_time}</b>\n"
        f"💰 Цена: <b>{booking_price} ₽</b>\n\n"
        f"{'💡 LED-наращивание +200 ₽' if led else ''}\n\n"
        "Ждём вас! 💗",
        parse_mode="HTML",
    )

    await callback.answer(
        "Запись создана! ✅"
    )


# ============================================================
# 🧮 РАСЧЁТ СВОБОДНЫХ СЛОТОВ
# ============================================================

def build_free_slots(
    master,
    service,
    selected_date,
    bookings,
):
    work_start = datetime.strptime(
        master.work_start,
        "%H:%M",
    )

    work_end = datetime.strptime(
        master.work_end,
        "%H:%M",
    )

    duration = service.duration_min

    now = datetime.now()

    current = work_start

    slots = []

    while current + timedelta(minutes=duration) <= work_end:
        slot_start = current
        slot_end = current + timedelta(
            minutes=duration
        )

        # Для сегодняшнего дня не показываем прошедшее время
        if selected_date == date.today():
            current_datetime = datetime.combine(
                selected_date,
                slot_start.time(),
            )

            if current_datetime <= now:
                current += timedelta(minutes=10)
                continue

        start_text = slot_start.strftime("%H:%M")
        end_text = slot_end.strftime("%H:%M")

        if not has_overlap(
            start_time=start_text,
            end_time=end_text,
            bookings=bookings,
        ):
            slots.append(
                (start_text, end_text)
            )

        current += timedelta(minutes=10)

    return slots


# ============================================================
# 🚫 ПРОВЕРКА ПЕРЕСЕЧЕНИЯ
# ============================================================

def has_overlap(
    start_time,
    end_time,
    bookings,
):
    new_start = datetime.strptime(
        start_time,
        "%H:%M",
    )

    new_end = datetime.strptime(
        end_time,
        "%H:%M",
    )

    for booking in bookings:
        existing_start = datetime.strptime(
            booking.booking_time,
            "%H:%M",
        )

        existing_end = (
            existing_start
            + timedelta(minutes=booking.duration_min)
        )

        if (
            new_start < existing_end
            and new_end > existing_start
        ):
            return True

    return False

# ============================================================
# 🛠 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def format_price(
    price_from: int,
    price_to: int,
) -> str:

    if price_from == price_to:
        return f"{price_from:,}".replace(",", " ")

    return (
        f"{price_from:,}".replace(",", " ")
        + "–"
        + f"{price_to:,}".replace(",", " ")
    )


def format_duration(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60

    if hours and mins:
        return f"{hours} ч {mins} мин"

    if hours:
        return f"{hours} ч"

    return f"{mins} мин"


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

    return (
        f"{value.day} {months[value.month - 1]}"
    )
# ============================================================
# 📋 МОИ ЗАПИСИ
# ============================================================

@router.message(F.text == "📋 Мои записи")
async def my_bookings(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "📋 У вас пока нет записей."
            )
            return

        result = await session.execute(
            select(Booking)
            .where(
                Booking.user_id == user.id,
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
                "📋 <b>У вас нет активных записей.</b>",
                parse_mode="HTML",
            )
            return

        for booking in bookings:
            result = await session.execute(
                select(Master).where(
                    Master.id == booking.master_id
                )
            )
            master = result.scalar_one_or_none()

            result = await session.execute(
                select(Service).where(
                    Service.id == booking.service_id
                )
            )
            service = result.scalar_one_or_none()

            master_name = (
                master.name
                if master
                else "Неизвестный мастер"
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

            print("DEBUG LED:", booking.id, booking.led, type(booking.led)) 

            await message.answer(
                "📋 <b>Ваша запись</b>\n\n"
                f"👩 Мастер: <b>{master_name}</b>\n"
                f"💅 Услуга: <b>{service_name}</b>\n"
                f"📅 Дата: <b>{format_date(booking_date)}</b>\n"
                f"🕐 Время: <b>"
                f"{booking.booking_time}–{end_time}"
                f"</b>\n"
                f"💰 Цена: <b>{booking.price} ₽</b>\n"
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
# ============================================================
# 👤 ПОЛУЧИТЬ ID ПОЛЬЗОВАТЕЛЯ
# ============================================================

async def get_user_id(telegram_id: int) -> int | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            return None

        return user.id

# ============================================================
# ❌ ОТМЕНА ЗАПИСИ — ПОДТВЕРЖДЕНИЕ
# ============================================================

@router.callback_query(
    F.data.startswith("booking_cancel:")
)
async def booking_cancel(callback: CallbackQuery):
    booking_id = int(
        callback.data.split(":", 1)[1]
    )

    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.id == booking_id
            )
        )

        booking = result.scalar_one_or_none()

    if booking is None:
        await callback.answer(
            "Запись не найдена.",
            show_alert=True,
        )
        return

    if booking.user_id != await get_user_id(
        callback.from_user.id
    ):
        await callback.answer(
            "Это не ваша запись.",
            show_alert=True,
        )
        return

    if booking.status != "confirmed":
        await callback.answer(
            "Эта запись уже отменена.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "⚠️ <b>Отменить запись?</b>\n\n"
        "Вы действительно хотите отменить эту запись?\n\n"
        "После отмены это время снова станет доступно "
        "для других клиентов.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, отменить",
                        callback_data=(
                            f"booking_cancel_confirm:"
                            f"{booking.id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="↩️ Оставить запись",
                        callback_data=(
                            f"booking_cancel_back:"
                            f"{booking.id}"
                        ),
                    )
                ],
            ]
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# ❌ ОТМЕНА ЗАПИСИ — ПОДТВЕРЖДЕНИЕ ОТМЕНЫ
# ============================================================

@router.callback_query(
    F.data.startswith("booking_cancel_confirm:")
)
async def booking_cancel_confirm(callback: CallbackQuery):
    booking_id = int(
        callback.data.split(":", 1)[1]
    )

    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.id == booking_id
            )
        )

        booking = result.scalar_one_or_none()

        if booking is None:
            await callback.answer(
                "Запись не найдена.",
                show_alert=True,
            )
            return

        if booking.user_id != await get_user_id(
            callback.from_user.id
        ):
            await callback.answer(
                "Это не ваша запись.",
                show_alert=True,
            )
            return

        if booking.status != "confirmed":
            await callback.answer(
                "Эта запись уже отменена.",
                show_alert=True,
            )
            return

        booking.status = "cancelled"

        await session.commit()

    await callback.message.edit_text(
        "❌ <b>Запись отменена</b>\n\n"
        "Время снова доступно для записи.",
        parse_mode="HTML",
    )

    await callback.answer(
        "Запись отменена ✅"
    )


# ============================================================
# ↩️ ОТМЕНА — ВЕРНУТЬСЯ К ЗАПИСИ
# ============================================================

@router.callback_query(
    F.data.startswith("booking_cancel_back:")
)
async def booking_cancel_back(callback: CallbackQuery):
    booking_id = int(
        callback.data.split(":", 1)[1]
    )

    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.id == booking_id
            )
        )

        booking = result.scalar_one_or_none()

        if booking is None:
            await callback.answer(
                "Запись не найдена.",
                show_alert=True,
            )
            return

        if booking.user_id != await get_user_id(
            callback.from_user.id
        ):
            await callback.answer(
                "Это не ваша запись.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Master).where(
                Master.id == booking.master_id
            )
        )

        master = result.scalar_one_or_none()

        result = await session.execute(
            select(Service).where(
                Service.id == booking.service_id
            )
        )

        service = result.scalar_one_or_none()

    if master is None or service is None:
        await callback.answer(
            "Данные записи не найдены.",
            show_alert=True,
        )
        return

    start = datetime.strptime(
        booking.booking_time,
        "%H:%M",
    )

    end = start + timedelta(
        minutes=booking.duration_min
    )

    await callback.message.edit_text(
        "📋 <b>Моя запись</b>\n\n"
        f"💗 <b>{service.name}</b>\n"
        f"👩 Мастер: {master.name}\n"
        f"📅 Дата: {booking.booking_date}\n"
        f"🕐 Время: "
        f"{booking.booking_time}–{end.strftime('%H:%M')}\n"
        f"💰 Цена: {booking.price} ₽\n"
        f"{'💡 LED-наращивание +200 ₽' if booking.led else ''}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Перенести запись",
                        callback_data=(
                            f"booking_reschedule:{booking.id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отменить запись",
                        callback_data=(
                            f"booking_cancel:{booking.id}"
                        ),
                    )
                ],
            ]
        ),
        parse_mode="HTML",
    )

    await callback.answer()
# ============================================================
# 🔄 ПЕРЕНОС ЗАПИСИ — НАЧАЛО
# ============================================================
@router.callback_query(
    F.data.startswith("booking_reschedule:")
)
async def booking_reschedule(callback: CallbackQuery):
    booking_id = int(
        callback.data.split(":", 1)[1]
    )

    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.id == booking_id
            )
        )

        booking = result.scalar_one_or_none()

    if booking is None:
        await callback.answer(
            "Запись не найдена.",
            show_alert=True,
        )
        return

    if booking.user_id != await get_user_id(
        callback.from_user.id
    ):
        await callback.answer(
            "Это не ваша запись.",
            show_alert=True,
        )
        return

    if booking.status != "confirmed":
        await callback.answer(
            "Эту запись нельзя перенести.",
            show_alert=True,
        )
        return

    today = date.today()

    buttons = []

    for offset in range(14):
        current_date = today + timedelta(days=offset)

        buttons.append(
            InlineKeyboardButton(
                text=current_date.strftime("%d.%m"),
                callback_data=(
                    f"reschedule_date:"
                    f"{booking.id}:"
                    f"{current_date.isoformat()}"
                ),
            )
        )

    keyboard = []

    for i in range(0, len(buttons), 2):
        keyboard.append(
            buttons[i:i + 2]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="my_bookings_back",
            )
        ]
    )

    await callback.message.edit_text(
        "🔄 <b>Перенос записи</b>\n\n"
        "📅 Выберите новую дату:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )

    await callback.answer()
# ============================================================
# 🔄 ПЕРЕНОС ЗАПИСИ — ВЫБОР НОВОГО ВРЕМЕНИ
# ============================================================

@router.callback_query(
    F.data.startswith("reschedule_date:")
)
async def reschedule_date(callback: CallbackQuery):
    _, booking_id, selected_date = (
        callback.data.split(":", 2)
    )

    booking_id = int(booking_id)

    selected = date.fromisoformat(selected_date)

    if selected < date.today():
        await callback.answer(
            "Нельзя выбрать прошедшую дату.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.id == booking_id
            )
        )

        booking = result.scalar_one_or_none()

        if booking is None:
            await callback.answer(
                "Запись не найдена.",
                show_alert=True,
            )
            return

        if booking.user_id != await get_user_id(
            callback.from_user.id
        ):
            await callback.answer(
                "Это не ваша запись.",
                show_alert=True,
            )
            return

        if booking.status != "confirmed":
            await callback.answer(
                "Эту запись нельзя перенести.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Service).where(
                Service.id == booking.service_id,
                Service.is_active.is_(True),
            )
        )

        service = result.scalar_one_or_none()

        if service is None:
            await callback.answer(
                "Услуга больше недоступна.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Master).where(
                Master.id == booking.master_id,
                Master.is_active.is_(True),
            )
        )

        master = result.scalar_one_or_none()

        if master is None:
            await callback.answer(
                "Мастер больше недоступен.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Booking).where(
                Booking.master_id == master.id,
                Booking.booking_date == selected_date,
                Booking.status.in_(
                    ["confirmed", "pending"]
                ),
                Booking.id != booking.id,
            )
        )

        bookings = result.scalars().all()

    slots = build_free_slots(
        master=master,
        service=service,
        selected_date=selected,
        bookings=bookings,
    )

    if not slots:
        await callback.answer(
            "На эту дату свободного времени нет.",
            show_alert=True,
        )
        return

    keyboard = []
    row = []

    for slot_start, slot_end in slots:
        row.append(
            InlineKeyboardButton(
                text=f"🕐 {slot_start}",
                callback_data=(
                    f"reschedule_time:"
                    f"{booking.id}:"
                    f"{selected_date}:"
                    f"{slot_start}"
                ),
            )
        )

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                text="◀️ Выбрать другую дату",
                callback_data=(
                    f"booking_reschedule:{booking.id}"
                ),
            )
        ]
    )

    await callback.message.edit_text(
        "🔄 <b>Перенос записи</b>\n\n"
        f"💅 {service.name}\n"
        f"📅 {format_date(selected)}\n"
        f"⏱ {format_duration(service.duration_min)}\n\n"
        "🕐 Выберите новое время:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )

    await callback.answer()
# ============================================================
# 🔄 ПЕРЕНОС ЗАПИСИ — ПОДТВЕРЖДЕНИЕ НОВОГО ВРЕМЕНИ
# ============================================================

@router.callback_query(
    F.data.startswith("reschedule_time:")
)
async def reschedule_time(callback: CallbackQuery):
    _, booking_id, selected_date, new_time = (
        callback.data.split(":", 3)
    )

    booking_id = int(booking_id)

    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.id == booking_id
            )
        )

        booking = result.scalar_one_or_none()

        if booking is None:
            await callback.answer(
                "Запись не найдена.",
                show_alert=True,
            )
            return

        if booking.user_id != await get_user_id(
            callback.from_user.id
        ):
            await callback.answer(
                "Это не ваша запись.",
                show_alert=True,
            )
            return

        if booking.status != "confirmed":
            await callback.answer(
                "Эту запись нельзя перенести.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Service).where(
                Service.id == booking.service_id,
                Service.is_active.is_(True),
            )
        )

        service = result.scalar_one_or_none()

        if service is None:
            await callback.answer(
                "Услуга больше недоступна.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Master).where(
                Master.id == booking.master_id,
                Master.is_active.is_(True),
            )
        )

        master = result.scalar_one_or_none()

        if master is None:
            await callback.answer(
                "Мастер больше недоступен.",
                show_alert=True,
            )
            return

        start = datetime.strptime(
            new_time,
            "%H:%M",
        )

        end = start + timedelta(
            minutes=service.duration_min
        )

        end_time = end.strftime("%H:%M")

        result = await session.execute(
            select(Booking).where(
                Booking.master_id == master.id,
                Booking.booking_date == selected_date,
                Booking.status.in_(
                    ["confirmed", "pending"]
                ),
                Booking.id != booking.id,
            )
        )

        existing_bookings = result.scalars().all()

        if has_overlap(
            start_time=new_time,
            end_time=end_time,
            bookings=existing_bookings,
        ):
            await callback.answer(
                "😔 Это время уже заняли. Выберите другое.",
                show_alert=True,
            )
            return

        old_date = booking.booking_date
        old_time = booking.booking_time

        booking.booking_date = selected_date
        booking.booking_time = new_time
        booking.duration_min = service.duration_min

        await session.commit()

    await callback.message.edit_text(
        "🔄 <b>Запись перенесена!</b>\n\n"
        f"👩 Мастер: <b>{master.name}</b>\n"
        f"💅 Услуга: <b>{service.name}</b>\n"
        f"📅 Новая дата: <b>"
        f"{format_date(date.fromisoformat(selected_date))}"
        f"</b>\n"
        f"🕐 Новое время: <b>"
        f"{new_time}–{end_time}"
        f"</b>\n"
        f"💰 Цена: <b>{booking.price} ₽</b>\n"
        f"{'💡 LED-наращивание +200 ₽' if booking.led else ''}\n\n"
        "💗 Ваша запись успешно перенесена!",
        parse_mode="HTML",
    )

    await callback.answer(
        "Запись перенесена ✅"
    )