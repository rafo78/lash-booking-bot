from aiogram import Router, F
from aiogram.types import Message


router = Router()


@router.message(F.text == "ℹ️ О сервисе")
async def about_handler(message: Message):
    await message.answer(
        "ℹ️ <b>О СЕРВИСЕ</b>\n\n"
        "💗 Lash Beauty Booking — сервис онлайн-записи "
        "к мастерам по наращиванию ресниц.\n\n"
        "Здесь вы можете:\n"
        "📅 записаться к мастеру\n"
        "💰 посмотреть услуги и цены\n"
        "📸 посмотреть портфолио\n"
        "📍 узнать адрес мастера\n"
        "📋 посмотреть свои записи\n\n"
        "Мы делаем запись удобной, быстрой и доступной "
        "в любое время суток. 💕"
    )