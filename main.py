import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers.start import router as start_router
from bot.handlers.booking import router as booking_router
from bot.handlers.portfolio import router as portfolio_router
from bot.handlers.address import router as address_router
from bot.handlers.about import router as about_router
from bot.handlers.master import router as master_router
from bot.handlers.services import router as services_router
from bot.handlers.master_cabinet import router as master_cabinet_router
from database.database import init_database


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не найден в файле .env"
    )


dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(booking_router)
dp.include_router(portfolio_router)
dp.include_router(address_router)
dp.include_router(about_router)
dp.include_router(master_router)
dp.include_router(services_router)
dp.include_router(master_cabinet_router)


async def main():
    await init_database()

    bot = Bot(token=BOT_TOKEN)

    print("🤖 Запускаю Telegram-бота...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())