from collections import defaultdict

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.database import async_session
from database.models import Master, Service


router = Router()


@router.message(F.text == "💰 Услуги и цены")
async def services_handler(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Master)
            .where(Master.name == "Полечка")
        )

        master = result.scalar_one_or_none()

        if master is None:
            await message.answer(
                "❌ Информация о мастере пока недоступна."
            )
            return

        result = await session.execute(
            select(Service)
            .where(
                Service.master_id == master.id,
                Service.is_active.is_(True),
            )
            .order_by(Service.id)
        )

        services = result.scalars().all()

    if not services:
        await message.answer(
            "😔 Сейчас услуги недоступны."
        )
        return

    categories = defaultdict(list)

    for service in services:
        categories[service.category].append(service)

    category_titles = {
        "Коррекция": "💗 Коррекция наращенных ресниц",
        "Наращивание": "💕 Наращивание ресниц",
        "Снятие": "🖤 Снятие",
    }

    text_parts = [
        f"💗 <b>УСЛУГИ И ЦЕНЫ</b>\n"
        f"Мастер: <b>{master.name}</b>\n"
    ]

    category_order = [
        "Коррекция",
        "Наращивание",
        "Снятие",
    ]

    for category in category_order:
        if category not in categories:
            continue

        text_parts.append(
            f"\n<b>{category_titles.get(category, category)}</b>\n"
        )

        for service in categories[category]:
            if service.price_from == service.price_to:
                price = f"{service.price_from:,}".replace(",", " ")
            else:
                price = (
                    f"{service.price_from:,}".replace(",", " ")
                    + "–"
                    + f"{service.price_to:,}".replace(",", " ")
                )

            if service.duration_min == service.duration_max:
                duration = format_duration(service.duration_min)
            else:
                duration = (
                    f"{format_duration(service.duration_min)}"
                    f"–"
                    f"{format_duration(service.duration_max)}"
                )

            text_parts.append(
                f"• {service.name}\n"
                f"  {price} ₽ · {duration}\n"
            )

    await message.answer(
        "\n".join(text_parts),
        parse_mode="HTML",
    )


def format_duration(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60

    if hours and mins:
        return f"{hours} ч {mins} мин"

    if hours:
        return f"{hours} ч"

    return f"{mins} мин"