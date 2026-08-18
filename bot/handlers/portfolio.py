from aiogram import Router, F
from aiogram.types import Message


router = Router()


@router.message(F.text == "📸 Портфолио")
async def portfolio_handler(message: Message):
    await message.answer(
        "📸 <b>ПОРТФОЛИО ПОЛЕЧКИ</b>\n\n"
        "Здесь скоро появятся работы Полечки 💗\n\n"
        "Мы обязательно добавим фотографии "
        "и сделаем красивую галерею работ.",
        parse_mode="HTML",
    )