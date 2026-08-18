from aiogram import Router, F
from aiogram.types import Message


router = Router()


@router.message(F.text == "📍 Адреса")
async def address_handler(message: Message):
    await message.answer(
        "📍 <b>АДРЕС ПОЛЕЧКИ</b>\n\n"
        "👩 Мастер: <b>Полечка</b>\n"
        "🏙 Город: <b>Рязань</b>\n"
        "📍 Адрес: <b>ул. Чапаева, 59</b>\n\n"
        "🕐 Время работы: <b>10:00–20:00</b>",
        parse_mode="HTML",
    )